import json
import random
import sys
from datetime import datetime, timedelta

import humanize
import redis
import requests

from flask import make_response

from constants import (
    DATA_NODES,
    LISTEN_PORT,
    MASTER_KEY,
    MASTER_TTL,
    EXPIRED_PREFIX,
    NODES_TTL,
    R_PREFIX,
    SERVICE_PORT,
)


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
    if ttl is not None:
        conn.expire(_key, ttl)


def r_master_etag(conn, value=None):
    if value:
        r_set(conn, f"{MASTER_KEY}:ETAG", value, ttl=None)
    else:
        etag, _ = r_get(conn, f"{MASTER_KEY}:ETAG")
        return etag


# remember if some key was expired earlier
def r_log_expire(conn, key, ttl):
    _key = f"{EXPIRED_PREFIX}:{key}"
    r_set(conn, _key, "1", ttl=ttl)


def r_was_expired(conn, key):
    _key = f"{EXPIRED_PREFIX}:{key}"
    value, _ = r_get(conn, _key)
    return value == "1"


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
