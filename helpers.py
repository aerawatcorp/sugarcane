
import json
import random
import sys
from datetime import datetime, timedelta

import humanize
import redis
import requests

from constants import (DATA_NODES, LISTEN_PORT, MASTER_KEY, MASTER_TTL,
                        NODES_TTL, R_PREFIX, SERVICE_PORT)

from flask import make_response


def verify_redis_connection(conn):
    # Verify if redis is running, by simply fetching a TTL value
    conn.ttl("{R_PREFIX}{MASTER_KEY}")

def r_expires_on(ttl):
    return datetime.now() + timedelta(seconds=ttl)


def r_get(conn, key):
    _key = f"{R_PREFIX}:{key}"
    ttl = conn.ttl(_key) or None
    if ttl == -2:
        return None, False

    val = conn.get(_key)
    if val is not None:
        val = json.loads(val)
    else:
        ttl = False

    return val, ttl


def r_set(conn, key, value, ttl=None):
    _key = f"{R_PREFIX}:{key}"
    conn.set(_key, json.dumps(value))
    conn.expire(_key, ttl)


def json_response(data):
    response = make_response(json.dumps(data))
    response.headers["Content-Type"] = "application/json"
    return response

def humanize_delta(date):
    return humanize.precisedelta(
        datetime.now() - datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f"),
        minimum_unit="seconds",
    )

