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

def rebuild_all_fake_data(directory=True, conn=None):
    all_nodes_info, all_nodes_data = fake_all_nodes()
    master_data = fake_master_data(all_nodes_info)

    if directory is False and conn is None:
        return master_data, all_nodes_info, all_nodes_data

    # for nodes
    for node_name, node_data in all_nodes_data.items():
        version = node_data["version"]
        if directory:
            node_dir = os.path.join(CONTENT_ROOT, "nodes/", node_name)
            if not os.path.exists(node_dir):
                os.makedirs(node_dir)
            node_file = os.path.join(node_dir, f"{version}.json")
            latest_node_file = os.path.join(node_dir, "latest.json")
            with open(node_file, "w") as f:
                print(f'Writing node {node_name}@{node_data["version"]} to {node_file}')
                f.write(json.dumps(node_data, indent=4, sort_keys=True))
            with open(latest_node_file, "w") as f:
                print(f'Writing node {node_name}@{node_data["version"]} to {latest_node_file}')
                f.write(json.dumps(node_data, indent=4, sort_keys=True))
        if conn:
            r_set(conn, f"{node_name}:{node_data['version']}", node_data, ttl=NODES_TTL)

    # for master
    if directory:
        master_file = os.path.join(CONTENT_ROOT, "master.json")
        with open(master_file, "w") as f:
            print(f'Writing master to {master_file}')
            f.write(json.dumps(master_data, indent=4, sort_keys=True))
    if conn:
        r_set(conn, MASTER_KEY, master_data, ttl=MASTER_TTL)

if __name__ == "__main__":
    from redis_client import r1
    rebuild_all_fake_data(directory=True, conn=r1)