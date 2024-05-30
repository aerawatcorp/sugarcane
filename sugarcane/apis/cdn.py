import pytz
import requests

from datetime import datetime
from dateutil.parser import parse
from flask import Blueprint, abort
from flask import request
from urllib.parse import urlencode

from sugarlib.constants import (
    NODES_TTL,
    MASTER_KEY,
    MASTER_KEY_VERBOSED,
    MASTER_TTL,
    MASTER_JAGGERY_API_URL,
    NODE_JAGGERY_API_URL,
)
from sugarcane.core.helpers import json_response
from sugarlib.helpers import etag_master, etag_node
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import (
    r_get,
    r_log_expire,
    r_master_etag,
    r_set,
)


blueprint = Blueprint("cdn", __name__)


@blueprint.route("/master/", methods=["GET"])
def master():
    """Get nodes meta data"""
    # Retrieve data from in memory cache
    cached_master, ttl = r_get(r1, MASTER_KEY_VERBOSED)

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

        for _, v in (master_data.get("nodes") or {}).items()    :
            v.pop("version")
            v.pop("updated_on")

        r_set(r1, MASTER_KEY_VERBOSED, master_data, ttl=MASTER_TTL)
        
        etag = etag_master(master_data["updated_on"])
        r_master_etag(r1, etag)
        return json_response(data=master_data, headers={"X-Cache": "MISS"}, etag=etag)
    else:
        abort(503)


@blueprint.route("/r/<version>/<node_name>", methods=["GET"])
def node(version, node_name):
    """Get nodes data"""
    args_dict = request.args.to_dict()
    sub_catalog = urlencode(args_dict) if args_dict else "root"
    versioned_key = f"{node_name}-{sub_catalog}:{version}"
    verbosed_versioned_key = f"{node_name}-{sub_catalog}-v:{version}"
    etag = etag_node(node_name, version)

    # Retrieve data from in memory cache
    node_data, node_ttl = r_get(r1, versioned_key)

    if node_ttl is not False:
        # Return cache HIT data
        return json_response(node_data, headers={"X-Cache": "HIT"}, etag=etag)

    if NODE_JAGGERY_API_URL:
        print("Retrieve and return data")
        response = requests.get(
            NODE_JAGGERY_API_URL.format(node_name=node_name), params=request.args
        )
        if not response.ok:
            print(response.content)
            print("Could not fetch data")
            abort(503)

        node_data = response.json()
        
        expires_on = node_data["expires_on"]
        expires_on_datetime = parse(expires_on, fuzzy=True)

        ttl_seconds = (expires_on_datetime - datetime.now(pytz.utc)).seconds

        # Set in memory cache in case of cache MISS
        r_set(r1, versioned_key, node_data, ttl=ttl_seconds)
        r_set(r1, verbosed_versioned_key, node_data, ttl=MASTER_TTL)
        return json_response(
            node_data,
            headers={"X-Cache": "MISS"},
            etag=etag,
        )
    else:
        abort(503)
