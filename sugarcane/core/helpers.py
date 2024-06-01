import json

from flask import request
from flask import make_response


def get_request_data():
    """Get flask request data"""
    if request.is_json:
        return request.get_json()
    else:
        return request.form.to_dict()


def json_response(data, is_json=False, headers={}, etag=None):
    response = make_response(json.dumps(data, indent=4) if is_json is False else data)
    response.headers["Content-Type"] = "application/json"
    for k, v in headers.items():
        response.headers[k] = v
    if etag:
        response.headers["Etag"] = etag
    return response


def cache_hit_headers():
    return {"X-Cache": "HIT"}


def cache_miss_headers():
    return {"X-Cache": "MISS"}
