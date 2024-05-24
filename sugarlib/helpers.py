import json
import random
import sys
import humanize
import redis
import requests

from datetime import datetime, timedelta


def humanize_delta(date_value):
    return humanize.precisedelta(
        datetime.now() - datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S.%f"),
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

def get_expires_on_ttl(expires_datetime):
    ttl = (datetime.strptime(expires_datetime, "%Y-%m-%d %H:%M:%S.%f") - datetime.now()).total_seconds()
    if ttl < 0:
        return False
    return int(ttl)