import requests
import pytz

from datetime import datetime
from dateutil.parser import parse

from core.init import flask_app
from core.helpers import cache_miss_headers, cache_hit_headers
from sugarcane.helpers.dataclass import NodeResponse, EmptyNodeResponse
from sugarcane.helpers.exceptions import ServiceUnavailableException
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_set, r_get
from sugarlib.constants import JAGGERY_BASE_URL, NODE_JAGGERY_API_URL, MASTER_TTL
from sugarlib.helpers import etag_node, build_url


def fetch_node_data(version, node_name, sub_catalog=None, params={}, headers={}):
    if not NODE_JAGGERY_API_URL:
        raise ServiceUnavailableException

    etag = etag_node(node_name, version)

    versioned_key = f"{node_name}-{sub_catalog}:{version}"
    verbosed_versioned_key = f"{node_name}-{sub_catalog}-v:{version}"

    flask_app.logger.info(
        f"[NODE] Initiate retrieve {verbosed_versioned_key} node data"
    )
    url = build_url(JAGGERY_BASE_URL, NODE_JAGGERY_API_URL.format(node_name=node_name))
    response = requests.get(url, params=params, headers=dict(headers))
    if not response.ok:
        flask_app.logger.error(
            f"[NODE] Could not fetch {verbosed_versioned_key} node data {response.content}"
        )
        raise ServiceUnavailableException

    node_data = response.json()
    expires_on = node_data["expires_on"]
    expires_on_datetime = parse(expires_on, fuzzy=True)

    ttl_seconds = (expires_on_datetime - datetime.now(pytz.utc)).seconds

    # Set verbose and terse data in in-memory cache in case of cache MISS
    flask_app.logger.info(f"[NODE] Set {versioned_key} data in cache")
    r_set(r1, versioned_key, node_data, ttl=ttl_seconds)

    flask_app.logger.info(f"[NODE] Set {verbosed_versioned_key} data in cache")
    r_set(r1, verbosed_versioned_key, node_data, ttl=MASTER_TTL)

    # Set latest version meta in cachenode_response
    r_set(r1, f"{node_name}:version", node_data["version"])
    return NodeResponse(
        data=node_data, headers=cache_miss_headers(), etag=etag, status=True
    )


def fetch_cached_node_data(version, node_name, sub_catalog=None) -> NodeResponse:
    """Get nodes data"""
    verbosed_versioned_key = f"{node_name}-{sub_catalog}-v:{version}"
    etag = etag_node(node_name, version)

    # Retrieve data from in memory cache
    node_data, node_ttl = r_get(r1, verbosed_versioned_key)

    if node_ttl is not False:
        flask_app.logger.info(
            f"[NODE] Return {verbosed_versioned_key} node data from cache"
        )
        # Return cache HIT data
        return NodeResponse(
            data=node_data, headers=cache_hit_headers(), etag=etag, status=True
        )

    return EmptyNodeResponse()
