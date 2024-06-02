import requests
import traceback
import logging

from datetime import timedelta, datetime
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify

from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_set, r_get, r_delete
from sugarlib.constants import (
    MASTER_TTL,
    NODE_API_URL,
    REQUEST_TIMEOUT,
)

from sachet.exceptions import (
    WriteToCacheError,
    CacheBuildAlreadyInitiated,
    InvalidSubCatalogException,
)
from helpers.models import BaseModel
from helpers.misc import get_local_time, get_local_isotime


logger = logging.getLogger(__name__)


class Catalog(BaseModel):
    """Sachet information related to catalog"""

    name = models.CharField(max_length=255, db_index=True, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    namespace = models.CharField(max_length=255, null=True, blank=True)

    provider = models.CharField(max_length=255, db_index=True)
    provider_url = models.URLField()
    sub_catalogs = ArrayField(
        models.CharField(max_length=255, blank=True), null=True, blank=True
    )

    cache_rule = models.JSONField(default=dict, blank=True)
    trigger_rule = models.JSONField(default=dict, blank=True)

    ttl = models.IntegerField(
        default=100,
        help_text=_("Default time to live in seconds for the catalog sachets"),
    )
    is_live = models.BooleanField(
        default=False,
        help_text=_(
            "If set to true, the client should directly initiate request ignoring the cache"
        ),
    )
    latest_version = models.CharField(max_length=255, null=True, blank=True)
    latest_expiry = models.DateTimeField(null=True, blank=True)

    @property
    def is_expired(self):
        return self.latest_expiry < get_local_time() if self.latest_expiry else True

    def __str__(self) -> str:
        return self.name

    def _slugify(self) -> str:
        if not self.slug:
            name = self.name.replace("/", "-")
            self.slug = slugify(name)
        return self.slug

    def save(self, *args, **kwargs):
        self._slugify()
        return super().save(*args, **kwargs)

    def get_node_url(self) -> str:
        """The url from which the current node data is retrieved"""
        return NODE_API_URL.format(node_name=self.slug, version=self.latest_version)

    def get_or_create_latest_store(
        self, sub_catalog: str = None, force: bool = False, **kwargs
    ) -> "Sachet":
        """Get latest sachet with version
        :param force: If set to true will force to get latest sachet disregarding the expiry date.
        """
        if sub_catalog and sub_catalog not in self.sub_catalogs:
            raise InvalidSubCatalogException(f"Invalid {sub_catalog} for catalog")

        sachet: Sachet = self.sachets.filter(
            version=self.latest_version,
            is_active=True,
            sub_catalog=sub_catalog,
            is_obsolete=False,
        ).last()

        if (
            not sachet
            or sachet.is_expired
            or self.is_expired
            or self.latest_version is None
            or force
        ):
            sachet = self.fetch_main_catalog_content(**kwargs)

            if sub_catalog:
                sachet = self.fetch_sub_catalog_content(sub_catalog, **kwargs)
        return sachet

    @classmethod
    def can_build_cache(self, key: str) -> bool:
        """Check if cache build can be initiated"""
        _, ttl = r_get(r1, key)
        if ttl is False:
            return True
        return False

    def start_build_lock(self, sub_catalog: str = "root"):
        """Start the build by initiating the cache"""
        if Catalog.can_build_cache(f"catalog-status:{self.id}:{sub_catalog}") is False:
            raise CacheBuildAlreadyInitiated(
                f"Cache build has already been iniiated for - {self.id} sub catalog - {sub_catalog}"
            )

        # Set the key in cache with ttl to match request timeout
        r_set(r1, f"catalog-status:{self.id}:{sub_catalog}", True, ttl=REQUEST_TIMEOUT)

    def end_build_lock(self, sub_catalog: str = "root"):
        """Remove the key from cache"""
        r_delete(r1, f"catalog-status:{self.id}:{sub_catalog}")

    @transaction.atomic
    def fetch_sub_catalog_content(self, sub_catalog: str, **kwargs):
        """Build new version of the sachet"""
        if sub_catalog and sub_catalog not in self.sub_catalogs:
            raise InvalidSubCatalogException(f"Invalid {sub_catalog} for catalog")

        try:
            self.start_build_lock(sub_catalog)

            expires_on = get_local_time() + timedelta(seconds=self.ttl)

            sachet = Sachet.new(
                self,
                sub_catalog,
                expires_on,
                self.latest_version,
                fetch_content=True,
                **kwargs,
            )

            self.end_build_lock(sub_catalog)
        except Exception as exp:
            logger.error(
                f"[CATALOG BUILD] Build new catalog ({self.name}) for {sub_catalog} error"
                f"\n{exp} {traceback.format_exc()}"
            )
            self.end_build_lock(sub_catalog)
            raise WriteToCacheError("Could not build new sachet")

        return sachet

    @transaction.atomic
    def fetch_main_catalog_content(self, **kwargs):
        """Build new version of the sachet"""
        try:
            self.start_build_lock()

            now = get_local_time()
            expires_on = now + timedelta(seconds=self.ttl)

            version_by_timestamp = int(now.timestamp())
            sachet = Sachet.new(
                self,
                None,
                expires_on,
                version_by_timestamp,
                fetch_content=True,
                **kwargs,
            )

            obj = Catalog.objects.select_for_update().get(pk=self.pk)
            obj.latest_version = version_by_timestamp
            obj.latest_expiry = expires_on
            obj.save(update_fields=["updated_on", "latest_version", "latest_expiry"])

            self.end_build_lock()
        except Exception as exp:
            logger.error(
                f"[CATALOG BUILD] Build new catalog ({self.name}) error"
                f"\n{exp} {traceback.format_exc()}"
            )
            self.end_build_lock()
            raise WriteToCacheError("Could not build new sachet")

        return sachet

    @classmethod
    def get_master_schema(cls):
        """Build master schema"""
        now = get_local_time()
        expires_on = now + timedelta(seconds=MASTER_TTL)
        cache_data = {
            "expires_on": str(get_local_isotime(expires_on)),
            "scheme": "master",
            "updated_on": str(get_local_isotime(now)),
            "nodes": {},
        }

        # Get the distinct catalogs list
        expires_on_subquery = Sachet.objects.filter(
            catalog=OuterRef("pk"), version=OuterRef("latest_version")
        ).values("expires_on")[:1]

        # Annotate the Catalog queryset with the expires_on field from the subquery,
        # and use Coalesce to handle None values
        catalogs = (
            Catalog.objects.filter(
                is_obsolete=False,
                latest_version__isnull=False,
                latest_expiry__isnull=False,
            )
            .annotate(expires_on=Coalesce(Subquery(expires_on_subquery), Value(None)))
            .order_by("-id")
        )

        nodes = {}
        for i in catalogs:
            node_data = {
                "expires_on": (
                    str(get_local_isotime(i.latest_expiry)) if i.latest_expiry else None
                ),
                "url": i.get_node_url(),
                "is_live": i.is_live,
                "subs": i.sub_catalogs,
                "latest_version": i.latest_version,
                "version": i.latest_version,
                "updated_on": str(i.updated_on),
            }
            nodes.update({i.name: node_data})

        cache_data["nodes"] = nodes

        return cache_data, expires_on


class Sachet(BaseModel):
    """Sachet information related to cataolog sachet"""

    catalog = models.ForeignKey(
        Catalog, on_delete=models.PROTECT, related_name="sachets"
    )
    sub_catalog = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(help_text=_("URL to get the data from"))

    has_content = models.BooleanField(
        default=False,
        help_text=_("If sachet is not yet ready with the cached content set to False"),
    )
    content = models.JSONField(default=dict, blank=True)

    version = models.CharField(help_text=_("Version of the retrieved data"))
    expires_on = models.DateTimeField()

    is_active = models.BooleanField(
        default=True, help_text=_("Define if the version sachet is active")
    )
    remarks = models.CharField(max_length=255, null=True, blank=True)

    @property
    def is_expired(self):
        return self.expires_on < get_local_time()

    class Meta:
        unique_together = ["catalog", "sub_catalog", "version"]

    @classmethod
    @transaction.atomic
    def new(
        cls,
        catalog: Catalog,
        sub_catalog: str,
        expires_on: datetime,
        version: str,
        fetch_content: bool = False,
        **kwargs,
    ):
        """
        Create a new sachet for the catalog.
        Expecting the sachet to be the latest version for the catalog.
        """
        old_version_sachet = cls.objects.filter(
            catalog=catalog, sub_catalog=sub_catalog
        ).last()
        if old_version_sachet:
            old_version_sachet.is_active = False
            old_version_sachet.save(update_fields=["is_active", "updated_on"])

        obj, _ = cls.objects.get_or_create(
            catalog=catalog,
            sub_catalog=sub_catalog,
            version=version,
            defaults={
                "url": catalog.provider_url,
                "expires_on": expires_on,
                "is_active": True,
                "has_content": False,
                "content": {},
            },
        )
        if fetch_content:
            obj.fetch_and_write_to_db(**kwargs)
        return obj

    def _get_accepted_headers(self, headers):
        accepted_headers = ["authorization", "content-type"]
        new_headers = {}
        for key, value in headers.items():
            if key in accepted_headers:
                new_headers.update({key: value})

        return new_headers

    def request_data(self, headers: dict = {}) -> dict:
        """Get new data from request url"""
        response = requests.get(
            self.url,
            timeout=REQUEST_TIMEOUT,
            headers=self._get_accepted_headers(dict(headers)),
        )
        if not response.ok:
            logger.error(
                f"[SACHET] Fetch data error idx - {self.idx} \n{response.content}"
            )
            raise WriteToCacheError(
                f"[SACHET CACHE] Error response from ({self.url}) for sachet idx - {self.idx}"
            )
        return response.json()

    def get_node_schema(self):
        """Build node schema"""

        data = {
            "scheme": "node",
            "node": self.catalog.name,
            "version": self.version,
            "expires_on": str(get_local_isotime(self.expires_on)),
            "updated_on": str(get_local_isotime(self.updated_on)),
            "sub_catalog": self.sub_catalog,
            "data": self.content,
        }
        return data, self.expires_on

    def fetch_and_write_to_db(self, **kwargs):
        """Write to db"""
        now = get_local_time()

        # Get data from request
        data = self.request_data(headers=kwargs.get("headers") or {})

        self.content = data
        self.has_content = True
        self.expires_on = now + timedelta(seconds=self.catalog.ttl)
        self.save()
