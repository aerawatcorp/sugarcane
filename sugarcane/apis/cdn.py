import os
import json
import pytz
import requests

from datetime import datetime
from dateutil.parser import parse

from flask import Blueprint
from flask import Blueprint, abort

from sugarlib.constants import (
    CONTENT_ROOT, EXPIRED_TTL, MASTER_KEY, MASTER_TTL, MASTER_JAGGERY_API_URL, NODE_JAGGERY_API_URL
)
from sugarcane.core.helpers import json_response
from sugarlib.helpers import etag_master, etag_node
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import (
    r_get, r_log_expire, r_master_etag, r_set, r_was_expired
)


blueprint = Blueprint("cdn", __name__)


@blueprint.route("/master/", methods=["GET"])
def master():
    """Get nodes meta data"""
    # Retrieve data from in memory cache
    cached_master, ttl = r_get(r1, MASTER_KEY)
    
    if ttl is not False:
        # TODO - Add prints in logging instead
        print("Return data from cache")
        # Return cache HIT data
        return json_response(
            cached_master,
            is_json=True,
            headers={
                "X-Cache": "HIT",
                "Etag": etag_master(cached_master["updated_on"]),
            },
        )

    # In case of cache MISS, retrieve the data
    if MASTER_JAGGERY_API_URL:
        print("Retrieve and return data")
        response = requests.get(MASTER_JAGGERY_API_URL)
        if not response.ok:
            print(response.content)
            print("Could not fetch data")
            abort(503)
        
        master_data = response.json()
        
        # Set in memory cache in case of cache MISS
        r_set(r1, MASTER_KEY, master_data, ttl=MASTER_TTL) 
        etag = etag_master(master_data["updated_on"])
        r_master_etag(r1, etag)
        return json_response(data=master_data, headers={"X-Cache": "MISS"}, etag=etag)
    else:
        abort(503)


@blueprint.route("/get/<version>/<node_name>", methods=["GET"])
def node(version, node_name):
    """Get nodes data"""
    versioned_key = f"{node_name}:{version}"
    etag = etag_node(node_name, version)

    # Retrieve data from in memory cache
    node_data, node_ttl = r_get(r1, versioned_key)

    if node_ttl is not False:
        # Return cache HIT data
        return json_response(node_data, headers={"X-Cache": "HIT"}, etag=etag)
    
    if NODE_JAGGERY_API_URL:
        print("Retrieve and return data")
        response = requests.get(NODE_JAGGERY_API_URL.format(node_name=node_name))
        if not response.ok:
            print(response.content)
            print("Could not fetch data")
            abort(503)
        
        node_data = response.json()

        expires_on = node_data["expires_on"]
        expires_on_datetime = parse(expires_on, fuzzy=True)

        if expires_on_datetime < datetime.now(pytz.utc):
            # this was supposed to expire only
            r_log_expire(r1, versioned_key, EXPIRED_TTL)
            abort(503)
        
        # remaining seconds
        ttl_seconds = (expires_on_datetime - datetime.now(pytz.utc)).seconds
        r_set(r1, versioned_key, node_data, ttl=ttl_seconds)
        return json_response(
            node_data,
            headers={"X-Cache": "MISS"},
            etag=etag,
        )
    else:
        abort(503)
