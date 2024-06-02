from flask import Blueprint, abort
from flask import request
from urllib.parse import urlencode

from sugarcane.core.helpers import json_response, get_request_data
from sugarcane.helpers.cdn import (
    fetch_node_data,
    fetch_cached_node_data,
    fetch_cached_master_data,
    fetch_master_data,
    fetch_latest_node_version,
)
from sugarcane.helpers.exceptions import ServiceUnavailableException


blueprint = Blueprint("cdn", __name__)


@blueprint.route("/master/", methods=["GET"])
def master():
    """Get nodes meta data"""
    master_node_data = fetch_cached_master_data()
    if master_node_data and master_node_data.status is True:
        return master_node_data.json_response()

    try:
        master_node_response = fetch_master_data()
        return master_node_response.json_response()
    except ServiceUnavailableException as exp:
        abort(503, exp.message)


@blueprint.route("/r/<version>/<node_name>/", methods=["GET"])
def node(version, node_name):
    """Get nodes data"""
    args_dict = request.args.to_dict()
    sub_catalog = urlencode(args_dict) if args_dict else "_"

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


@blueprint.route("/composite/<context>/", methods=["POST"])
def composite(context):
    """Composite API to retrieve multiple node data"""
    data = get_request_data()

    response_data = {}

    for key, value in data.items():
        url_name = value["url_name"]
        url_name = url_name[1:] if url_name.startswith("/") else url_name

        split_url_name = url_name.split("/", 3)

        if len(split_url_name) != 3:
            response_data.update({key: {"status": 503, "data": {}}})

        version, node_name = split_url_name[1], split_url_name[2]
        query_params = value["params"]
        sub_catalog = urlencode(query_params) if query_params else "_"

        node_response = fetch_cached_node_data(version, node_name, sub_catalog)
        node_data = {}

        if node_response.status is True:
            node_data = node_response.data
        else:
            try:
                node_response = fetch_node_data(
                    version, node_name, sub_catalog, query_params, dict(request.headers)
                )
                node_data = node_response.data
            except ServiceUnavailableException:
                pass

        response_data.update(
            {
                key: {
                    "status": 200 if node_response.status is True else 503,
                    "data": node_data.get("data"),
                    "expires_on": node_data.get("expires_on"),
                    "version": node_data.get("version"),
                }
            }
        )

    return json_response(response_data, headers={"X-Cache": "COMPOSITE"})


@blueprint.route("/latest/<node_name>/", methods=["GET"])
def latest_node(node_name):
    """Get latest node name data"""
    args_dict = request.args.to_dict()
    sub_catalog = urlencode(args_dict) if args_dict else "_"

    version = fetch_latest_node_version(node_name=node_name, sub_catalog=sub_catalog)

    if version:
        node_response = fetch_cached_node_data(version, node_name, sub_catalog)
        if node_response.status is True:
            return node_response.json_response()

    abort(503, "Node latest data not found.")
