import logging

from django.db.models import Q

from jaggery.celery import app
from sachet.models import Catalog

from helpers.misc import get_local_time

logger = logging.getLogger(__name__)


@app.task
def fetch_catalog_content(catalog_id, sub_catalog=None):
    """Fetch catalog content"""
    catalog = Catalog.objects.get(id=catalog_id)
    
    catalog.fetch_main_catalog_content()

    if sub_catalog:
        catalog.fetch_sub_catalog_content(sub_catalog)
        return True

    for sub_catalog in catalog.sub_catalogs:
        catalog.fetch_sub_catalog_content(sub_catalog)
    return True


@app.task
def fetch_expired_catalogs_content():
    """Fetch the expired catalogs contents"""

    now = get_local_time()
    catalogs = Catalog.objects.filter(Q(latest_expiry__lte=now) | Q(latest_expiry__isnull=True), is_obsolete=False, is_live=False)
    for i in catalogs:
        fetch_catalog_content.delay(i.id)
    return True
