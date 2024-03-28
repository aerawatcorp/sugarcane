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

from ..sugarlib.constants import (
    DATA_NODES,
    MASTER_KEY,
    MASTER_TTL,
    NODES_TTL,
    R_PREFIX,
    CANE_SERVER_HOST, 
    CANE_SERVER_PORT,
    DEMO_APP_HOST,
    DEMO_APP_PORT    
)

from helpers import humanize_delta, verify_redis_connection
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
    app.register_blueprint(mock_app_blueprint)

    # run
    app.run(debug=True, port=DEMO_APP_PORT, host=DEMO_APP_HOST)