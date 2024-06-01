import pytz
import requests

from datetime import datetime
from dateutil.parser import parse
from flask import Blueprint, abort
from flask import request
from urllib.parse import urlencode

from core.init import flask_app
from sugarlib.constants import (
    MASTER_KEY,
    MASTER_KEY_VERBOSED,
    MASTER_TTL,
    JAGGERY_BASE_URL,
    MASTER_JAGGERY_API_URL,
    NODE_JAGGERY_API_URL,
)
from sugarcane.core.helpers import (
    json_response,
    get_request_data,
    cache_hit_headers,
    cache_miss_headers,
)
from sugarlib.helpers import etag_master, etag_node, build_url
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_get, r_master_etag, r_set


blueprint = Blueprint("cdn", __name__)


@blueprint.route("/master/", methods=["GET"])
def master():
    """Get nodes meta data"""
    # Retrieve data from in memory cache
    cached_master, ttl = r_get(r1, MASTER_KEY_VERBOSED)

    if ttl is not False:
        flask_app.logger.info("[MASTER] Return master data from cache")
        # Return cache HIT data
        _headers = cache_hit_headers()
        _headers.update({"Etag": etag_master(cached_master["updated_on"])})
        return json_response(
            cached_master,
            is_json=True,
            headers=_headers,
        )

    if not MASTER_JAGGERY_API_URL:
        abort(503, "Master data not available. Please check the configuration")

    flask_app.logger.info("[MASTER] Initiate retrieve master data")
    url = build_url(JAGGERY_BASE_URL, MASTER_JAGGERY_API_URL)
    response = requests.get(url, headers=dict(request.headers))
    if not response or not response.ok:
        flask_app.logger.error(
            f"[MASTER] JAGGERY ERROR : Could not fetch master data {response.content}"
        )
        abort(503, "Unable to fetch master data")

    try:
        master_data = response.json()
    except Exception as e:
        flask_app.logger.error(
            f"[MASTER] JAGGERY ERROR :  Could not parse master data {e}"
        )
        abort(503, response.content)
        abort(404, response.content)
        abort(503, "Unable to read master. Please try again later. ")

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
    return json_response(data=master_data, headers=cache_miss_headers(), etag=etag)


@blueprint.route("/r/<version>/<node_name>", methods=["GET"])
def node(version, node_name):
    """Get nodes data"""
    args_dict = request.args.to_dict()
    sub_catalog = urlencode(args_dict) if args_dict else "root"
    versioned_key = f"{node_name}-{sub_catalog}:{version}"
    verbosed_versioned_key = f"{node_name}-{sub_catalog}-v:{version}"
    etag = etag_node(node_name, version)

    # Retrieve data from in memory cache
    node_data, node_ttl = r_get(r1, verbosed_versioned_key)

    if node_ttl is not False:
        flask_app.logger.info(
            f"[NODE] Return {verbosed_versioned_key} node data from cache"
        )
        # Return cache HIT data
        return json_response(node_data, headers=cache_hit_headers(), etag=etag)

    if NODE_JAGGERY_API_URL:
        flask_app.logger.info(
            f"[NODE] Initiate retrieve {verbosed_versioned_key} node data"
        )
        url = build_url(
            JAGGERY_BASE_URL, NODE_JAGGERY_API_URL.format(node_name=node_name)
        )
        response = requests.get(url, params=request.args, headers=dict(request.headers))
        if not response.ok:
            flask_app.logger.error(
                f"[NODE] Could not fetch {verbosed_versioned_key} node data {response.content}"
            )
            abort(503)

        node_data = response.json()
        expires_on = node_data["expires_on"]
        expires_on_datetime = parse(expires_on, fuzzy=True)

        ttl_seconds = (expires_on_datetime - datetime.now(pytz.utc)).seconds

        # Set in memory cache in case of cache MISS
        flask_app.logger.info(f"[NODE] Set {versioned_key} data in cache")
        r_set(r1, versioned_key, node_data, ttl=ttl_seconds)

        flask_app.logger.info(f"[NODE] Set {verbosed_versioned_key} data in cache")
        r_set(r1, verbosed_versioned_key, node_data, ttl=MASTER_TTL)
        return json_response(
            node_data,
            headers=cache_miss_headers(),
            etag=etag,
        )
    else:
        abort(503)


@blueprint.route("/composite/<context>", methods=["POST"])
def composite(context):
    """Composite API to retrieve multiple node data"""
    data = get_request_data()

    response_data = {}

    for key, value in data.items():
        split_url_name = value["url_name"].split("/", 3)

        if len(split_url_name) != 4:
            response_data.update({key: {"status": 503, "data": {}}})

        version, node_name = split_url_name[2], split_url_name[3]
        query_params = value["params"]

        # TODO: test_request_context ??
        with flask_app.test_request_context(
            f"/r/{version}/{node_name}",
            query_string=query_params,
            headers=dict(request.headers),
        ):
            response = node(version, node_name)

        response_data.update(
            {key: {"status": 200, "data": response.json["data"]}}
        )  # TODO: Response should be resonse.json only, as we are not decorating the response as of now

    return json_response(response_data, headers={"X-Cache": "COMPOSITE"})


@blueprint.route("/latest/<catalog_name>", methods=["GET"])
def latest_node(catalog_name):
    # Fetch the latest version and respond that
    # @TODO:
    return json_response({})
