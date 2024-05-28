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
from helpers.misc import get_local_time


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

	def build_node_schema(self):
		"""Build node schema"""
		now = get_local_time()
		expires_on = now + timedelta(seconds=NODES_TTL)

		return {
			"scheme": "node",
			"node": self.catalog.name,
			"version": self.version,
			"expires_on": str(expires_on),
			"updated_on": str(self.updated_on),
			"data": self.content
		}
	
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
		cache_data = self.build_node_schema()
		r_set(r1, self.get_cache_redis_key(), cache_data, ttl=self.catalog.ttl)
	
	def invalidate_cache(self):
		"""Validate cache and write to cache"""
		try:
			self.validate_cache()
		except DatabaseCacheExpired:
			logger.info(f"[STORE] Initiate db write protocol for idx - {self.idx}")
			self.write_to_db()
			self.write_to_redis()

		except RedisCacheExpired:
			logger.info(f"[STORE] Initiate redis cache write protocol for idx - {self.idx}")

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
			raise DatabaseCacheExpired("Invalid 3rd level cache")
	