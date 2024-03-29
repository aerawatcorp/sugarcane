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
    CANE_SERVER_LISTEN_HOST, 
    CANE_SERVER_LISTEN_PORT,
    MASTER_KEY,
    MASTER_TTL,
    NODES_TTL,
    R_PREFIX,
)

from sugarlib.helpers import humanize_delta
from sugarlib.redis_helpers import verify_redis_connection
from sugarcane.server import sugarcane_blueprint

# Create a Flask application
app = Flask(__name__)
app.jinja_options["extensions"] = ["jinja2_humanize_extension.HumanizeExtension"]
app.jinja_env.filters["humanize_delta"] = humanize_delta

from sugarlib.redis_client import r1_cane as r1

# Verify if redis is running
try:
    verify_redis_connection(r1)
except Exception as exc:
    sys.exit(f"REDIS Exception : {exc}")

# Run the app
if __name__ == "__main__":
    # flask routes
    app.register_blueprint(sugarcane_blueprint)

    # run
    app.run(debug=True, port=CANE_SERVER_LISTEN_PORT, host=CANE_SERVER_LISTEN_HOST)
