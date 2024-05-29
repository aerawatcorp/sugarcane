import logging

from jaggery.celery import app

from sachet.models import Catalog
from sachet.exceptions import CacheBuildAlreadyInitiated

logging = logging.getLogger(__name__)


@app.task
def initiate_node_rebuild(catalog_id: int, sub_catalog: str):
    """Create a new version store for the catalog"""
    can_build = Catalog.can_build_cache(f"catalog-status:{catalog_id}:{sub_catalog}")
    if can_build is False:
        logging.info(
            f"[NODE REBUILD ERROR] Catalog ({catalog_id}:{sub_catalog}) node rebuild already initaited"
        )
        return True

    catalog = Catalog.objects.get(id=catalog_id)
    logging.info(
        f"[NODE REBUILD INITIATED] Catalog ({catalog.name}:{sub_catalog}) node rebuild initiated"
    )
    try:
        catalog.build_new_store(sub_catalog)
    except CacheBuildAlreadyInitiated:
        logging.info(
            f"[NODE REBUILD ERROR] Catalog ({catalog.name}:{sub_catalog}) node rebuild already initaited"
        )
        return True

    logging.info(
        f"[NODE REBUILD COMPLETED] Catalog ({catalog.name}:{sub_catalog}) node rebuild completed"
    )
