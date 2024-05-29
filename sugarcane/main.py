import os
import sys

from decouple import AutoConfig

config = AutoConfig(search_path="/app")

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(BASE_DIR)

from core.init import flask_app     # noqa

if __name__ == "__main__":
    flask_app.run(
        debug=config("DEBUG"),
        port=config("CANE_SERVER_LISTEN_PORT"),
        host=config("CANE_SERVER_LISTEN_HOST"),
    )
