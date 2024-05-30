import os

from logging.config import dictConfig
from flask import Flask
from decouple import AutoConfig

config = AutoConfig(search_path="/app")

LOG_FILE_PATH = os.path.expanduser("~") + "/sugarcane.log"

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.FileHandler",
                "filename": LOG_FILE_PATH,
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "django.request": {
                "handlers": ["default"],
                "level": "WARN",
                "propagate": False,
            },
        },
    }
)

flask_app = Flask(__name__)
flask_app.config.from_object("core.settings")


def routes_initialize():
    """Initialize routes"""
    from core.urls import blueprints

    for bp in blueprints:
        flask_app.register_blueprint(bp[0], url_prefix=bp[1])

    return flask_app


routes_initialize()
