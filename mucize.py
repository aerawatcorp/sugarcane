"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

from flask import Blueprint
from helpers import json_response, r_get
from faker import master
from redis_client import r1

mucize_blueprint = Blueprint("mucize", __name__)

# Define a route for the home page
@mucize_blueprint.route("/cdn/master")
def cdn_master():
    return json_response(master(conn=r1))


@mucize_blueprint.route("/cdn/get/<version>/<node_name>")
def cdn_node(version, node_name):
    versioned_key = f"{node_name}:{version}"
    node_data, node_ttl = r_get(r1, versioned_key)
    print(node_data, node_ttl)
    if node_ttl is False:
        abort(404)
    return json_response(node_data)
