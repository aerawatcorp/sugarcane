"""
A Flask implementation of cache where a meta cache and individual cache
is implemented in versioned, for a proper delivery, not to compromise
the data availability and accuracy 
"""

from flask import Flask, request, make_response, abort
import redis
import json
import random
from datetime import datetime, timedelta
import requests

# Create a Flask application
app = Flask(__name__)
app.jinja_options["extensions"] = ["jinja2_humanize_extension.HumanizeExtension"]

# Redis connection 1
r1 = redis.StrictRedis(host="localhost", port=6379, db=0)

# Redis connection 2
r2 = redis.StrictRedis(host="localhost", port=6379, db=1)

R_PREFIX = "cdn:blinds:"
MASTER_KEY = "MASTER"
MASTER_TTL = 10
NODES_TTL = 100


def r_expires_on(ttl):
    return datetime.now() + timedelta(seconds=ttl)


def r_get(conn, key):
    _key = f"{R_PREFIX}:{key}"
    print(_key)
    ttl = conn.ttl(_key) or None
    if ttl == -2:
        return None, False

    val = conn.get(_key)
    print(val, _key, ttl)
    if val is not None:
        val = json.loads(val)
    else:
        ttl = False

    return val, ttl


def r_set(conn, key, value, ttl=None):
    _key = f"{R_PREFIX}:{key}"
    conn.set(_key, json.dumps(value))
    conn.expire(_key, ttl)


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

    nodes = ["post", "user", "food", "emoji", "people"]

    node_urls = {}

    for node_name in nodes:
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


def master():
    master_data, ttl = r_get(r1, MASTER_KEY)
    if ttl is False:
        populate_default_data(r1)
        master_data, ttl = r_get(r1, MASTER_KEY)

    master_data["ttl"] = ttl
    return master_data


def json_response(data):
    response = make_response(json.dumps(data))
    response.headers["Content-Type"] = "application/json"
    return response


# Define a route for the home page
@app.route("/cdn/master")
def cdn_master():
    return json_response(master())


@app.route("/cdn/get/<version>/<node_name>")
def cdn_node(version, node_name):
    versioned_key = f"{node_name}:{version}"
    node_data, node_ttl = r_get(r1, versioned_key)
    print(node_data, node_ttl)
    if node_ttl is False:
        abort(404)
    return json_response(node_data)


@app.template_filter("humanize_delta")
def humanize_delta(date):
    import humanize

    return humanize.precisedelta(
        datetime.now() - datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f"),
        # months=False,
        minimum_unit="seconds",
    )


@app.route("/")
def index():
    from views import index_view

    master_data = requests.get("http://localhost:5000/cdn/master").json()
    return index_view(ctx={"master_data": master_data, "now": datetime.now()})


@app.route("/browse/<node_name>")
def browse(node_name):
    from views import browse_view

    master_data = requests.get("http://localhost:5000/cdn/master").json()
    node_url = master_data["nodes"][node_name]["url"]
    node_data = requests.get(f"http://localhost:5000{node_url}").json()
    return browse_view(
        ctx={"master_data": master_data, "node_data": node_data, "now": datetime.now()}
    )


@app.errorhandler(404)
def page_not_found(error):
    return "404 Not Found", 404


# Run the app
if __name__ == "__main__":

    app.run(debug=True)
