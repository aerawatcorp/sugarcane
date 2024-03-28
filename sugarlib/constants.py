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

CANE_SERVER_LISTEN_HOST = "localhost"
CANE_SERVER_LISTEN_PORT = 8000

DEMO_APP_CANE_SERVER_HOST = "http://localhost:8000/"
DEMO_APP_HOST = "localhost"
DEMO_APP_PORT = 5000