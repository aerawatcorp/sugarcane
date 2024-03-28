import json
import random
import sys
from datetime import datetime, timedelta

import humanize
import redis
import requests
from flask import make_response

from sugarlib.constants import (DATA_NODES, EXPIRED_PREFIX, MASTER_KEY,
                                MASTER_TTL, NODES_TTL, R_PREFIX)


def json_response(data, is_json=False, headers={}, etag=None):
    response = make_response(json.dumps(data, indent=4) if is_json is False else data)
    response.headers["Content-Type"] = "application/json"
    for k, v in headers.items():
        response.headers[k] = v
    if etag:
        response.headers["Etag"] = etag
    return response


def humanize_delta(date):
    return humanize.precisedelta(
        datetime.now() - datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f"),
        minimum_unit="seconds",
    )


def etag_master(updated_on):
    _etag = updated_on.replace(" ", "").replace(":", "").replace("-", "")
    return f"MASTER.{_etag}"


def etag_node(node_name, version):
    return f"NODE.{node_name.upper()}.{version}"


def master_etag_verification(request, conn):
    etag = request.headers.get("If-None-Match")
    if etag:
        stored_etag = r_master_etag(conn)
        return stored_etag == etag
    return None
