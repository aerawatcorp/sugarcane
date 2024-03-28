# This is a mock application implementation in Flask

import random
import sys
from datetime import datetime, timedelta

import redis
import requests
from flask import Flask, abort, make_response, request, json

from sugarlib.constants import (DATA_NODES, MASTER_KEY, MASTER_TTL,
                        NODES_TTL, R_PREFIX, DEMO_APP_CANE_SERVER_HOST)

# @TODO : 
# Implement API caching in the demo application now

from flask import Blueprint

mock_app_blueprint = Blueprint('mock_app', __name__)

@mock_app_blueprint.route("/")
def index():
    from views import index_view
    master_data = requests.get(f"{DEMO_APP_CANE_SERVER_HOST}/cdn/master").json()
    return index_view(ctx={"master_data": master_data, "now": datetime.now()})


@mock_app_blueprint.route("/browse/<node_name>")
def browse(node_name):
    from views import browse_view

    master_data = requests.get(f"{DEMO_APP_CANE_SERVER_HOST}/cdn/master").json()
    node_url = master_data["nodes"][node_name]["url"]
    node_data = requests.get(f"{DEMO_APP_CANE_SERVER_HOST}{node_url}")
    if node_data.status_code != 200:
        return abort(404)
    return browse_view(
        ctx={"master_data": master_data, "node_data": node_data.json(), "now": datetime.now()}
    )


@mock_app_blueprint.errorhandler(404)
def page_not_found(error):
    return "404 Not Found", 404
