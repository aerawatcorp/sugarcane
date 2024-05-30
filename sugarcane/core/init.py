from flask import Flask
from decouple import AutoConfig

config = AutoConfig(search_path="/app")

flask_app = Flask(__name__)
flask_app.config.from_object("core.settings")


def routes_initialize():
    """Initialize routes"""
    from core.urls import blueprints

    for bp in blueprints:
        flask_app.register_blueprint(bp[0], url_prefix=bp[1])

    return flask_app


routes_initialize()
