from flask import Blueprint, abort
from flask import request
from urllib.parse import urlencode

from core.init import flask_app
from sugarcane.core.helpers import json_response, get_request_data
from sugarcane.helpers.cdn import (
    fetch_node_data,
    fetch_cached_node_data,
    fetch_cached_master_data,
    fetch_master_data,
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
