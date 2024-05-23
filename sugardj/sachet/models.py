import requests
import os
import traceback
import logging

from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils.dateparse import parse_datetime

from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_set, r_get
from sugarlib.constants import CONTENT_ROOT, MASTER_TTL, NODES_TTL, NODE_API_URL, MASTER_SCHEMA_PATH, MASTER_KEY

from sachet.exceptions import WriteToCacheError, CacheExpired
from helpers.models import BaseModel
from helpers.misc import get_local_time, FileHandler, build_url


logger = logging.getLogger(__name__)


class Catalog(BaseModel):
	"""Store information related to catalog"""
	name = models.CharField(max_length=255, db_index=True)
	namespace = models.CharField(max_length=255, null=True, blank=True)
	provider = models.CharField(max_length=255, db_index=True)
	provider_url = models.URLField()

	cache_rule = models.JSONField(default=dict, blank=True)
	trigger_rule = models.JSONField(default=dict, blank=True)

	ttl = models.IntegerField(default=100, help_text=_("Default time to live in seconds for the catalog stores"))

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
		unique_together = ["catalog", "url", "version"]
		
	def get_cache_file_path(self):
		return os.path.join(CONTENT_ROOT, f"nodes/{self.catalog.name}/{self.version}.json")
	
	def get_cache_redis_key(self):
		return f"{self.catalog.name}-{self.version}"

	def get_node_url(self):
		return NODE_API_URL.format(node_name=self.catalog.name, version=self.version)

	def get_data(self) -> dict:
		"""Get data from request url"""
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
			raise CacheExpired("Invalid 3rd level cache")
		
		try:
			data = FileHandler.read(self.get_cache_file_path())
			if parse_datetime(data["expires_on"]) < now:
				logger.error(f"[STORE] File cache invalid - {self.get_cache_file_path()} idx - {self.idx}")
				raise CacheExpired("Invalid 2nd level Cache")	
		except Exception as exp:
			logger.error(f"[STORE] File cache validation error - {self.get_cache_file_path()} idx - {self.idx} {exp} {traceback.format_exc()}")
			raise CacheExpired("Invalid 2nd level Cache")

		try:
			_, ttl = r_get(r1, self.get_cache_redis_key())
			if ttl is False:
				logger.error(f"[STORE] Redis cache invalid - {self.get_cache_redis_key()} idx - {self.idx}")
				raise CacheExpired("Invalid 1st level cache")
		except Exception as exp:
			logger.error(f"[STORE] Redis cache validation error - {self.get_cache_redis_key()} idx - {self.idx}")
			raise CacheExpired("Invalid 1st level cache")

	def write_to_cache(self, data):
		"""Write to cache"""
		now = get_local_time()

		# Store data in 3rd level cache
		self.content = data
		self.expires_on = now + timedelta(seconds=self.catalog.ttl)
		self.save()

		cache_data = {
			"scheme": "node",
			"node": self.catalog.name,
			"version": self.version,
			"expires_on": str(now),
			"updated_on": str(self.updated_on),
			"data": self.content
		}
		
		# TODO - Need to work in cache timing
		# Store data in 2nd level cache
		cache_data["expires_on"] = str(now + timedelta(seconds=int(self.catalog.ttl * 0.75)))
		FileHandler.write(self.get_cache_file_path(), cache_data)
		
		# Store data in 1st level cache
		cache_data["expires_on"] = str(now + timedelta(seconds=NODES_TTL))
		r_set(r1, self.get_cache_redis_key(), cache_data, ttl=self.catalog.ttl)
	
	@classmethod
	def write_master_schema_to_cache(cls):
		"""Write master schema to cache"""
		now = get_local_time()

		cache_data = {
			"expires_on": str(now + timedelta(seconds=MASTER_TTL)),
			"updated_on": str(now),
			"scheme": "master",
			"nodes": {}
		}
		
		stores = Store.objects.filter(is_obsolete=False, is_active=True).select_related("catalog")
		now = get_local_time()
		
		nodes = {}
		for i in stores:
			node_data = {
				"expires_on": str(i.expires_on),
				"updated_on": str(i.updated_on),
				"url": i.get_node_url(),
				"version": i.version
			}
			nodes.update({i.catalog.name: node_data})
		
		cache_data["nodes"] = nodes

		# TODO - Need to work in cache timing
		# Store data in 2nd level cache
		FileHandler.write(MASTER_SCHEMA_PATH, cache_data)
		
		# Store data in 1st level cache
		cache_data["expires_on"] = str(now + timedelta(seconds=MASTER_TTL))
		r_set(r1, {MASTER_KEY}, cache_data, ttl=MASTER_TTL)
