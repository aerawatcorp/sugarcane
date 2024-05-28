import requests
import logging

from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_set, r_get
from sugarlib.constants import CONTENT_ROOT, MASTER_TTL, NODES_TTL, NODE_API_URL, MASTER_SCHEMA_PATH, MASTER_KEY

from sachet.exceptions import WriteToCacheError, DatabaseCacheExpired, FileCacheExpired, RedisCacheExpired
from helpers.models import BaseModel
from helpers.misc import get_local_time, get_local_isotime


logger = logging.getLogger(__name__)


class Catalog(BaseModel):
	"""Store information related to catalog"""
	name = models.CharField(max_length=255, db_index=True, unique=True)
	namespace = models.CharField(max_length=255, null=True, blank=True)
	provider = models.CharField(max_length=255, db_index=True)
	provider_url = models.URLField()

	cache_rule = models.JSONField(default=dict, blank=True)
	trigger_rule = models.JSONField(default=dict, blank=True)

	ttl = models.IntegerField(default=100, help_text=_("Default time to live in seconds for the catalog stores"))
	is_live = models.BooleanField(default=False)
	latest_version = models.CharField(max_length=255)

	def __str__(self):
		return self.name

	def get_node_url(self):
		"""The url from which the current node data is retrieved"""
		# TODO - need to use slug in node name
		return NODE_API_URL.format(node_name=self.idx, version=self.latest_version)

	def get_lastest_store(self):
		"""Get latest store with version"""
		store = self.stores.filter(version=self.latest_version, is_active=True).last()
		return store

	@classmethod
	def get_master_schema(cls, verbose: bool=True):
		"""Build master schema"""
		now = get_local_time()
		expires_on = str(now + timedelta(seconds=MASTER_TTL))

		cache_data = {
			"expires_on": expires_on,
			"scheme": "master",
			"nodes": {}
		}
		if not verbose:
			cache_data.update({"updated_on": str(now)})
		
		# Get the distinct catalogs list
		expires_on_subquery = Store.objects.filter(
			catalog=OuterRef('pk'), 
			version=OuterRef('latest_version')
		).values('expires_on')[:1]

		# Annotate the Catalog queryset with the expires_on field from the subquery,
		# and use Coalesce to handle None values
		catalogs = Catalog.objects.filter(is_obsolete=False).annotate(
			expires_on=Coalesce(Subquery(expires_on_subquery), Value(None))
		).order_by("-id")

		nodes = {}
		for i in catalogs:
			node_data = {
				"expires_on": str(i.expires_on),
				"url": i.get_node_url(),
				"is_live": i.is_live,
			}
			if not verbose:
				node_data.update({
					"version": i.latest_version,
					"updated_on": str(i.updated_on),
				})

			nodes.update({i.name: node_data})
		
		cache_data["nodes"] = nodes

		return cache_data, expires_on

	@classmethod
	def write_master_schema_to_cache(cls):
		"""Write master schema in cache"""
		cache_data = cls.get_master_schema()
		r_set(r1, MASTER_KEY, cache_data, ttl=MASTER_TTL)

	@classmethod
	def get_master_schema_from_cache(cls):
		"""Write master schema in cache"""
		return r_get(r1, MASTER_KEY)


class Store(BaseModel):
	"""Store information related to cataolog store"""
	catalog = models.ForeignKey(Catalog, on_delete=models.PROTECT, related_name="stores")
	url = models.URLField(help_text=_("URL to get the data from"))
	content = models.JSONField(default=dict, blank=True)
	version = models.CharField(help_text=_("Version of the retrieved data"))
	expires_on = models.DateTimeField()
	
	is_active = models.BooleanField(default=True, help_text=_("Define if the version store is active"))
	remarks = models.CharField(max_length=255, null=True, blank=True)

	class Meta:
		unique_together = ["catalog", "version"]
		
	def get_cache_redis_key(self):
		return f"{self.catalog.name}-{self.version}"

	def request_data(self) -> dict:
		"""Get new data from request url"""
		response = requests.get(self.url)
		if not response.ok:
			logger.error(f"[STORE] Fetch data error idx - {self.idx}")
			raise WriteToCacheError(f"[STORE CACHE] Error response from ({self.url}) for store idx - {self.idx}")
		return response.json()

	def validate_cache(self):
		"""Validate expiry date of the cache"""
		now = get_local_time()
		
		if self.expires_on < now:
			logger.error(f"[STORE] DB cache invalid - {self.get_cache_file_path()} idx - {self.idx}")
			raise DatabaseCacheExpired("Invalid database level cache")

		try:
			_, ttl = r_get(r1, self.get_cache_redis_key())
			if ttl is False:
				logger.error(f"[STORE] Redis cache invalid - {self.get_cache_redis_key()} idx - {self.idx}")
				raise RedisCacheExpired("Invalid redis cache")
		except Exception as exp:
			logger.error(f"[STORE] Redis cache validation error - {self.get_cache_redis_key()} idx - {self.idx}")
			raise RedisCacheExpired("Invalid redis cache")

	def get_node_schema(self):
		"""Build node schema"""
		now = get_local_time()
		expires_on = now + timedelta(seconds=NODES_TTL)

		if expires_on > self.expires_on:
			expires_on = self.expires_on

		data = {
			"scheme": "node",
			"node": self.catalog.name,
			"version": self.version,
			"expires_on": str(get_local_isotime(expires_on)),
			"updated_on": str(get_local_isotime(self.updated_on)),
			"data": self.content
		}
		return data, expires_on
	
	def write_to_db(self):
		"""Write to db"""
		now = get_local_time()

		# Get data from request
		data = self.request_data()

		# Store data in 3rd level cache
		self.content = data
		self.expires_on = now + timedelta(seconds=self.catalog.ttl)
		self.save()

	def write_to_redis(self):
		"""Write to redis as 3rd level cache"""
		cache_data = self.get_node_schema()
		r_set(r1, self.get_cache_redis_key(), cache_data, ttl=self.catalog.ttl)
	
	def invalidate_cache(self):
		"""Validate cache and write to cache"""
		self.write_to_db()
		self.write_to_redis()

	def get_data(self):
		"""Validate mulitple level cached data's expiry date"""
		now = get_local_time()
		
		data, ttl = r_get(r1, self.get_cache_redis_key())
		if ttl is not False:
			logger.info(f"[STORE] Get redis cache data for idx - {self.idx}")
			return data

		if self.expires_on > now:
			logger.info(f"[STORE] Get db cache data for idx - {self.idx}")
			self.write_to_redis()
			return self.get_node_schema()
		else:
			self.invalidate_cache()
			return self.get_node_schema()
	