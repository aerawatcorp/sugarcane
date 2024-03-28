"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

import os
import json
import random
import sys
from datetime import datetime, timedelta

# To prevent relative import error
from pathlib import Path
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(BASE_DIR)

import requests
from flask import Flask, abort, make_response, request

from sugarlib.constants import (
    DATA_NODES,
    MASTER_KEY,
    MASTER_TTL,
    NODES_TTL,
    R_PREFIX,
    DEMO_APP_CANE_SERVER_HOST,
    DEMO_APP_HOST,
    DEMO_APP_PORT
)

from sugarlib.helpers import humanize_delta
from sugarlib.redis_helpers import verify_redis_connection
from demo_application.server import mock_app_blueprint

# Create a Flask application
app = Flask(__name__)
app.jinja_options["extensions"] = ["jinja2_humanize_extension.HumanizeExtension"]
app.jinja_env.filters["humanize_delta"] = humanize_delta

from sugarlib.redis_client import r2_demo

# Verify if redis is running
try:
    verify_redis_connection(r2_demo)
except Exception as exc:
    sys.exit(f"REDIS Exception : {exc}")

# Run the app
if __name__ == "__main__":
    # some random data initialization
    app.register_blueprint(mock_app_blueprint)

    # run
    app.run(debug=True, port=DEMO_APP_PORT, host=DEMO_APP_HOST)