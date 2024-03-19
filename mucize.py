"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

import os
import json
from datetime import datetime, timedelta

from flask import Blueprint, abort

from constants import CONTENT_ROOT, MASTER_KEY, EXPIRED_TTL, MASTER_TTL
from helpers import json_response, r_get, r_was_expired, r_log_expire, r_set
from redis_client import r1

mucize_blueprint = Blueprint("mucize", __name__)

# Define a route for the home page
@mucize_blueprint.route("/cdn/master")
def cdn_master():
    cached_master, ttl = r_get(r1, MASTER_KEY)
    if ttl is not False:
        return json_response(cached_master, is_json=False, headers={"X-Cache": "HIT"})

    # Presume that the master is not cached
    master_in_file = open(os.path.join(CONTENT_ROOT, "master.json"))
    master_in_file = json.load(master_in_file)
    r_set(r1, MASTER_KEY, master_in_file, ttl=MASTER_TTL) # @TODO: check the ttl for master in this case.
    return json_response(data=master_in_file, headers={"X-Cache": "MISS"})

@mucize_blueprint.route("/cdn/get/<version>/<node_name>")
def cdn_node(version, node_name):
    versioned_key = f"{node_name}:{version}"
    node_data, node_ttl = r_get(r1, versioned_key)
    if node_ttl is not False:
        return json_response(node_data, headers={"X-Cache": "HIT"})

    # check if it was expired earlier
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
        else:
            # remaining seconds
            ttl_seconds = (expires_on_datetime - datetime.now()).seconds
            r_set(r1, versioned_key, node_data, ttl=ttl_seconds)
            return json_response(node_data, headers={"X-Cache": "MISS"})
    else:
        # there is no file
        abort(404)