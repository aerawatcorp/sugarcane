import os
from decouple import config

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "../content/datadir/")
DATA_NODES = config("DATA_NODES", cast=lambda v: [x.strip() for x in v.split(",")])

REDIS_HOST_CANE = config("REDIS_HOST_CANE")
REDIS_PORT_CANE = config("REDIS_PORT_CANE")
REDIS_DB_CANE = config("REDIS_DB_CANE")

REDIS_HOST_DEMO = config("REDIS_HOST_DEMO")
REDIS_PORT_DEMO = config("REDIS_PORT_DEMO")
REDIS_DB_DEMO = config("REDIS_DB_DEMO")

R_PREFIX = "cane:"
MASTER_KEY = "MASTER"
EXPIRED_PREFIX = "EXPIRED"
EXPIRED_TTL = 86400

MASTER_TTL = 10
NODES_TTL = 100

CANE_SERVER_LISTEN_HOST = config("CANE_SERVER_LISTEN_HOST")
CANE_SERVER_LISTEN_PORT = config("CANE_SERVER_LISTEN_PORT")

DEMO_APP_CANE_SERVER_HOST = config("DEMO_APP_CANE_SERVER_HOST")
DEMO_APP_HOST = config("DEMO_APP_HOST")
DEMO_APP_PORT = config("DEMO_APP_PORT")