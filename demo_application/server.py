# This is a mock application implementation in Flask

import random
import sys
from datetime import datetime, timedelta

import redis
import requests
from flask import Flask, abort, make_response, request, json

from sugarlib.constants import (
    DATA_NODES,
    MASTER_KEY,
    MASTER_TTL,
    NODES_TTL,
    R_PREFIX,
    DEMO_APP_CANE_SERVER_HOST,
)
from demo_application.helpers import fetch_master_schema, fetch_node_data
from demo_application.views import index_view, browse_view

from flask import Blueprint

mock_app_blueprint = Blueprint("mock_app", __name__)


@mock_app_blueprint.route("/")
def index():
    master_data = fetch_master_schema()
    return index_view(ctx={"master_data": master_data, "now": datetime.now()})


@mock_app_blueprint.route("/browse/<node_name>")
def browse(node_name):
    master_data = fetch_master_schema()
    node_data = fetch_node_data(node_name)
    return browse_view(
        ctx={"master_data": master_data, "node_data": node_data, "now": datetime.now()}
    )


@mock_app_blueprint.errorhandler(404)
def page_not_found(error):
    return "404 Not Found", 404
