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
from sugarlib.constants import (
    JAGGERY_BASE_URL,
    NODE_JAGGERY_API_URL,
    MASTER_TTL,
    MASTER_KEY_VERBOSED,
    MASTER_JAGGERY_API_URL,
    MASTER_KEY,
)
from sugarlib.helpers import etag_node, build_url, etag_master, r_master_etag


def fetch_master_data(headers: dict = {}):
    if not MASTER_JAGGERY_API_URL:
        raise ServiceUnavailableException(
            "Master data not available. Please check the configuration"
        )

    flask_app.logger.info("[MASTER] Initiate retrieve master data")

    url = build_url(JAGGERY_BASE_URL, MASTER_JAGGERY_API_URL)
    response = requests.get(url, headers=headers)
    if not response or not response.ok:
        flask_app.logger.error(
            f"[MASTER] JAGGERY ERROR : Could not fetch master data {response.content}"
        )
        raise ServiceUnavailableException("Unable to fetch master data")

    try:
        master_data = response.json()
    except Exception as e:
        flask_app.logger.error(
            f"[MASTER] JAGGERY ERROR :  Could not parse master data {e}"
        )
        raise ServiceUnavailableException(
            "Unable to read master. Please try again later."
        )

    # Set in memory cache in case of cache MISS
    flask_app.logger.info("[MASTER] Set master data in cache")
    r_set(r1, MASTER_KEY, master_data, ttl=MASTER_TTL)

    for _, v in (master_data.get("nodes") or {}).items():
        # @TODO: Why are we popping these keys?
        v.pop("version", None)
        v.pop("updated_on", None)

    flask_app.logger.info("[MASTER] Set master verbose data in cache")
    r_set(r1, MASTER_KEY_VERBOSED, master_data, ttl=MASTER_TTL)

    # TODO: The implementation of etag needs to be revisited
    etag = etag_master(master_data["updated_on"])
    r_master_etag(r1, etag)

    return NodeResponse(master_data, headers=cache_miss_headers(), etag=etag)


def fetch_cached_master_data():
    # Retrieve data from in memory cache
    cached_master, ttl = r_get(r1, MASTER_KEY_VERBOSED)

    if ttl is not False:
        flask_app.logger.info("[MASTER] Return master data from cache")
        # Return cache HIT data
        _headers = cache_hit_headers()
        _headers.update({"Etag": etag_master(cached_master["updated_on"])})
        return NodeResponse(data=cached_master, headers=_headers, status=True)

    return EmptyNodeResponse()


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
