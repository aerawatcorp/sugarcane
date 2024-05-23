import os
import json

from datetime import datetime
from flask import Blueprint
from flask import Blueprint, abort

from sugarlib.constants import (
    CONTENT_ROOT, EXPIRED_TTL, MASTER_KEY, MASTER_TTL, MASTER_SCHEMA_PATH
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
        # Return cache HIT data
        return json_response(
            cached_master,
            is_json=True,
            headers={
                "X-Cache": "HIT",
                "Etag": etag_master(cached_master["updated_on"]),
            },
        )

    # In case of cache MISS, retrieve the data from file cache
    # Presume that the master is not cached
    if os.path.exists(MASTER_SCHEMA_PATH):
        master_in_file = open(MASTER_SCHEMA_PATH)
        master_in_file = json.load(master_in_file)

        expires_on = master_in_file["expires_on"]
        expires_on_datetime = datetime.strptime(expires_on, "%Y-%m-%d %H:%M:%S.%f")

        if expires_on_datetime < datetime.now():
            # TODO - Need to get master meta data incase of expiry ??
            abort(404)

        # Set in memory cache in case of cache MISS
        r_set(r1, MASTER_KEY, master_in_file, ttl=MASTER_TTL) 
        etag = etag_master(master_in_file["updated_on"])
        r_master_etag(r1, etag)
        return json_response(data=master_in_file, headers={"X-Cache": "MISS"}, etag=etag)
    else:
        abort(418)


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
    
    # check if it was expired earlier
    # TODO - Get new value and store or return expire ??
    if r_was_expired(r1, versioned_key):
        abort(404)

    # see in the file (this can be replaced with a replaceable function not necessarily file based)
    node_file = os.path.join(CONTENT_ROOT, "nodes/", node_name, f"{version}.json")

    if os.path.exists(node_file):
        node_data = open(node_file)
        node_data = json.load(node_data)
        expires_on = node_data["expires_on"]
        expires_on_datetime = datetime.strptime(expires_on, "%Y-%m-%d %H:%M:%S.%f")

        if expires_on_datetime < datetime.now():
            # this was supposed to expire only
            r_log_expire(r1, versioned_key, EXPIRED_TTL)
            abort(404)
        
        # remaining seconds
        ttl_seconds = (expires_on_datetime - datetime.now()).seconds
        r_set(r1, versioned_key, node_data, ttl=ttl_seconds)
        return json_response(
            node_data,
            headers={"X-Cache": "MISS"},
            etag=etag,
        )
    else:
        abort(404)
