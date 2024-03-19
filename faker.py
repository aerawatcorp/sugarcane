# A simple faker to generate dummy data for the static files

import json
import os
import random
from datetime import datetime, timedelta

from constants import (CONTENT_ROOT, DATA_NODES, MASTER_KEY, MASTER_TTL,
                       NODES_TTL)
from helpers import r_expires_on, r_get, r_set


def get_versioned_node_url(node_name, version):
    return f"/cdn/get/{version}/{node_name}"

def random_version():
    rand = f"{random.random() * 100000}"
    return "v" + rand[0:1] + "." + rand[1:2] + "." + rand[2:4]

def random_versioned_node_url(node_name):
    semver = random_version()
    return get_versioned_node_url(node_name, version), semver, node_name


def fake_master_data(node_urls):
    return {
        "scheme": "master",
        "expires_on": str(r_expires_on(MASTER_TTL)),
        "updated_on": str(datetime.now()),
        "nodes": node_urls,
    }

def fake_node_data(node_name, version=None, ttl=None):
    return {
        "scheme": "node",
        "node": node_name,
        "description": "This is some sample data for some node, that is consumed over the API",
        "version": version or random_version(),
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


def fake_all_nodes():
    all_nodes = {}
    all_nodes_data = {}
    for node_name in DATA_NODES:
        version = random_version()
        all_nodes[node_name] = {
            "url": get_versioned_node_url(node_name, version),
            "version": version,
            "expires_on": str(r_expires_on(NODES_TTL)),
            "updated_on": str(datetime.now())
        }
        all_nodes_data[node_name] = fake_node_data(node_name, version=version, ttl=NODES_TTL)
    return all_nodes, all_nodes_data

def write_everything_fake_to_content_dir():
    all_nodes_info, all_nodes_data = fake_all_nodes()
    for node_name, node_data in all_nodes_data.items():
        node_file = os.path.join(CONTENT_ROOT, "nodes/", node_name + ".json")
        with open(node_file, "w") as f:
            print(f'Writing node {node_name} to {node_file}')
            f.write(json.dumps(node_data, indent=4, sort_keys=True))
    
    master_file = os.path.join(CONTENT_ROOT, "master.json")
    with open(master_file, "w") as f:
        print(f'Writing master to {master_file}')
        f.write(json.dumps(all_nodes_info, indent=4, sort_keys=True))

if __name__ == "__main__":
    write_everything_fake_to_content_dir()

# def load_to_():
#     for all_nodes_fake_data in fake_all_nodes():
#     node_urls = {}
#     for node_name in DATA_NODES:
#         _url, semver, _ = random_versioned_node_url(node_name)
#         node_urls[node_name] = {
#             "url": _url,
#             "version": semver,
#             "expires_on": str(r_expires_on(NODES_TTL)),
#             "updated_on": str(datetime.now()),
#         }
#         node_data = fake_node_data(node_name, version=semver, ttl=NODES_TTL)
#         # r_set(conn, f"{node_name}:{semver}", node_data, ttl=NODES_TTL)

#     master_data = fake_master_data(node_urls)
#     # r_set(conn, MASTER_KEY, master_data, ttl=MASTER_TTL)

# def populate_default_data(conn):
#     node_urls = {}

#     for node_name in DATA_NODES:
#         _url, semver, _ = _random_versioned_node_url(node_name)
#         node_urls[node_name] = {
#             "url": _url,
#             "version": semver,
#             "expires_on": str(r_expires_on(NODES_TTL)),
#             "updated_on": str(datetime.now()),
#         }
#         node_data = random_node_data(node_name, version=semver, ttl=NODES_TTL)
#         r_set(conn, f"{node_name}:{semver}", node_data, ttl=NODES_TTL)

#     master_data = {
#         "ttl": MASTER_TTL,
#         "expires_on": str(r_expires_on(MASTER_TTL)),
#         "updated_on": str(datetime.now()),
#         "nodes": node_urls,
#     }
#     r_set(conn, MASTER_KEY, master_data, ttl=MASTER_TTL)


# def master(conn):
#     master_data, ttl = r_get(conn, MASTER_KEY)
#     if ttl is False:
#         populate_default_data(conn)
#         master_data, ttl = r_get(conn, MASTER_KEY)

#     master_data["ttl"] = ttl
#     return master_data