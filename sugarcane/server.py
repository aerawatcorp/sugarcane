"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

import json
import os
from datetime import datetime, timedelta

from flask import Blueprint, abort, make_response, request

from sugarlib.constants import (CONTENT_ROOT, EXPIRED_TTL, MASTER_KEY,
                                MASTER_TTL)
from sugarlib.helpers import (etag_master, etag_node, json_response,
                              master_etag_verification)
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import (r_get, r_log_expire, r_master_etag, r_set,
                                    r_was_expired)

sugarcane_blueprint = Blueprint("sugarcane", __name__)

@sugarcane_blueprint.route("/")
def home():
    return json_response(
        {
            "message": "Welcome to the Sugarcane Server",
            "apis": {
                "master": "/cdn/master",
                "nodes": "/cdn/get/<version>/<node_name>",
            }
        }
    )


# Define a route for the home page
@sugarcane_blueprint.route("/cdn/master")
def cdn_master():
    if master_etag_verification(request, r1) is True:
        return make_response("", 304)
    cached_master, ttl = r_get(r1, MASTER_KEY)
    if ttl is not False:
        return json_response(
            cached_master,
            is_json=True,
            headers={
                "X-Cache": "HIT",
                "Etag": etag_master(cached_master["updated_on"]),
            },
        )

    # Presume that the master is not cached
    master_in_file = open(os.path.join(CONTENT_ROOT, "master.json"))
    master_in_file = json.load(master_in_file)
    r_set(
        r1, MASTER_KEY, master_in_file, ttl=MASTER_TTL
    )  # @TODO: check the ttl for master in this case.
    etag = etag_master(master_in_file["updated_on"])
    r_master_etag(r1, etag)
    return json_response(data=master_in_file, headers={"X-Cache": "MISS"}, etag=etag)


@sugarcane_blueprint.route("/cdn/get/<version>/<node_name>")
def cdn_node(version, node_name):
    versioned_key = f"{node_name}:{version}"
    etag = etag_node(node_name, version)
    node_data, node_ttl = r_get(r1, versioned_key)
    if node_ttl is not False:
        return json_response(node_data, headers={"X-Cache": "HIT"}, etag=etag)
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
            return json_response(
                node_data,
                headers={"X-Cache": "MISS"},
                etag=etag,
            )
    else:
        # there is no file
        abort(404)
