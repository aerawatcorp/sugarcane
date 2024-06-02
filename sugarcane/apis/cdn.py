import requests

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
)
from sugarcane.core.helpers import (
    json_response,
    get_request_data,
    cache_hit_headers,
    cache_miss_headers,
)
from sugarcane.helpers.cdn import fetch_node_data, fetch_cached_node_data
from sugarcane.helpers.exceptions import ServiceUnavailableException
from sugarlib.helpers import etag_master, build_url
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

    node_response = fetch_cached_node_data(version, node_name, sub_catalog)
    if node_response.status is True:
        return node_response.json_response()

    try:
        node_response = fetch_node_data(
            version, node_name, sub_catalog, args_dict, request.headers
        )
        return node_response.json_response()
    except ServiceUnavailableException as exp:
        abort(503, exp.message)


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
            {
                key: {
                    "status": 200,
                    "data": response.json["data"],
                    "expires_on": response.json["expires_on"],
                    "version": response.json["version"],
                }
            }
        )

    return json_response(response_data, headers={"X-Cache": "COMPOSITE"})


@blueprint.route("/latest/<catalog_name>", methods=["GET"])
def latest_node(catalog_name):
    # Fetch the latest version and respond that
    # @TODO:
    return json_response({})
