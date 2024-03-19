# A simple faker to generate dummy data for the static files

from constants import DATA_NODES, MASTER_KEY, MASTER_TTL, NODES_TTL
from datetime import datetime, timedelta
from helpers import r_expires_on, r_get, r_set
import random

def random_node_data(node_name, version, ttl):
    return {
        "node": node_name,
        "description": "This is some sample data for some node, that is consumed over the API",
        "version": version,
        "expires_on": None if ttl is None else str(r_expires_on(ttl)),
        "updated_on": str(datetime.now()),
        "data": [
            {
                "id": idx,
                "value": f"https://picsum.photos/id/{random.choice(range(1, 1000))}/200/300?type={node_name}",
            }
            for idx in range(1, 10)
        ],
    }


def populate_default_data(conn):
    def _random_versioned_node_url(node_name):
        rand = f"{random.random() * 100000}"
        semver = "v" + rand[0:1] + "." + rand[1:2] + "." + rand[2:4]
        return f"/cdn/get/{semver}/{node_name}", semver, node_name

    node_urls = {}

    for node_name in DATA_NODES:
        _url, semver, _ = _random_versioned_node_url(node_name)
        node_urls[node_name] = {
            "url": _url,
            "version": semver,
            "expires_on": str(r_expires_on(NODES_TTL)),
            "updated_on": str(datetime.now()),
        }
        node_data = random_node_data(node_name, version=semver, ttl=NODES_TTL)
        r_set(conn, f"{node_name}:{semver}", node_data, ttl=NODES_TTL)

    master_data = {
        "ttl": MASTER_TTL,
        "expires_on": str(r_expires_on(MASTER_TTL)),
        "updated_on": str(datetime.now()),
        "nodes": node_urls,
    }
    r_set(conn, MASTER_KEY, master_data, ttl=MASTER_TTL)


def master(conn):
    master_data, ttl = r_get(conn, MASTER_KEY)
    if ttl is False:
        populate_default_data(conn)
        master_data, ttl = r_get(conn, MASTER_KEY)

    master_data["ttl"] = ttl
    return master_data
