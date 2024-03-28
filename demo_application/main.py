"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

import json
import random
import sys
from datetime import datetime, timedelta

import requests
from flask import Flask, abort, make_response, request

from constants import (
    DATA_NODES,
    LISTEN_PORT,
    MASTER_KEY,
    MASTER_TTL,
    NODES_TTL,
    R_PREFIX,
    SERVICE_PORT,
)

from helpers import humanize_delta, verify_redis_connection
from sugarcane import sugarcane_blueprint
from app import mock_app_blueprint

# Create a Flask application
app = Flask(__name__)
app.jinja_options["extensions"] = ["jinja2_humanize_extension.HumanizeExtension"]
app.jinja_env.filters["humanize_delta"] = humanize_delta

from redis_client import r1

# Verify if redis is running
try:
    verify_redis_connection(r1)
except Exception as exc:
    sys.exit(f"REDIS Exception : {exc}")

# Run the app
if __name__ == "__main__":
    # some random data initialization
    from faker import rebuild_all_fake_data

    rebuild_all_fake_data(directory=True, conn=r1)

    # flask routes
    app.register_blueprint(sugarcane_blueprint)
    app.register_blueprint(mock_app_blueprint)

    # run
    app.run(debug=True, port=LISTEN_PORT)
