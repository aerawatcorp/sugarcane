import logging

from jaggery.celery import app

from sachet.models import Catalog, Store

logging = logging.getLogger(__name__)


@app.task
def initiate_node_rebuild(catalog_id):
    """Rebuild catalog node"""
    catalog = Catalog.objects.get(id=catalog_id)
    logging.info(f"[NODE REBUILD INITIATED] Catalog ({catalog.name}) node rebuild {catalog.latest_version} initiated")
    store = catalog.get_lastest_store()
    store.invalidate_cache()
    logging.info(f"[NODE REBUILD COMPLETED] Catalog ({catalog.name}) node rebuild {catalog.latest_version} completed")
