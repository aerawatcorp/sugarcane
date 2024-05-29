import os
import logging.config

LOG_FILE_PATH = os.path.expanduser("~") + "/sugarcane.log"

LOGGING = {
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

logging.config.dictConfig(LOGGING)
