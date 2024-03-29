# This file contains helper functions for the demo application

import requests
from sugarlib.constants import NODES_TTL, DEMO_APP_R_PREFIX_MASTER, DEMO_APP_R_PREFIX_NODE, DEMO_APP_CANE_SERVER_HOST
from sugarlib.redis_client import r2_demo as conn
from sugarlib.redis_helpers import (
    r_expires_on, 
    r_get,
    r_set,
)
from sugarlib.helpers import get_expires_on_ttl

DEMO_APP_CANE_SERVER_HOST = "http://sugarcane:8000"
def get_node_cache_key(node_name):
    return f"node:{node_name}"

def cached_request(url, cache_key=None, *args, **kwargs):
    """
    Make a request to the given URL and cache the response
    This works for GET requests only,
    limitation: doesn't work well with query params for now
    """
    if cache_key is None:
        cache_key = url.replace("/", "__")
    cached_response, ttl = r_get(conn, cache_key)
    if ttl is False or cached_response is None:
        url = f"{DEMO_APP_CANE_SERVER_HOST}{url}"
        _response = requests.get(url, *args, **kwargs)
        response = _response.json()
        expires_on = response.get('expires_on')
        ttl = get_expires_on_ttl(expires_on) if expires_on else NODES_TTL
        r_set(conn, cache_key, response, ttl=ttl)
        return response

    return cached_response

def fetch_master_schema(force_refresh=False):
    """
    Load the master schema from the Cane server
    """
    if force_refresh is False:
        master, ttl = r_get(conn, DEMO_APP_R_PREFIX_MASTER)
        if ttl is not False and ttl != -1:
            return master

    url = f"{DEMO_APP_CANE_SERVER_HOST}/cdn/master"
    _response = requests.get(url)
    response = _response.json()

    expires_on = response.get('expires_on', None)
    ttl = get_expires_on_ttl(expires_on) if expires_on else NODES_TTL
    if ttl is False:
        return response # Fallback, but the master already expired too
    r_set(conn, DEMO_APP_R_PREFIX_MASTER, response, ttl=ttl)
    return response

def fetch_node_data(node_name):
    """
    Load the data for the given node from the Cane server
    """
    def _node_object_from_master(node_name, force_master=False):
        master_data = fetch_master_schema(force_refresh=force_master)
        node_data = master_data["nodes"][node_name]
        expires_on = node_data.get('expires_on', None)
        ttl = get_expires_on_ttl(expires_on) if expires_on else NODES_TTL
        url = node_data["url"]
        return node_data, url, ttl
    _, node_url, ttl = _node_object_from_master(node_name)
    if ttl is False:
        _, node_url, ttl = _node_object_from_master(node_name, force_master=True)
    return cached_request(node_url, cache_key=get_node_cache_key(node_name))