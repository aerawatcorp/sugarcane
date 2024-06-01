from flask import Blueprint

from sugarcane.core.helpers import json_response


blueprint = Blueprint("index", __name__)


@blueprint.route("/", methods=["GET"])
def home():
    return json_response(
        {
            "message": "Welcome to the Sugarcane Server",
            "apis": {
                "master": "/master",
                "nodes": "/r/<version>/<slug>",
                "composite": "/composite/<context>",
            },
        }
    )
