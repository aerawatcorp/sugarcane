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

R_PREFIX = config("R_PREFIX")
MASTER_KEY = config("MASTER_KEY")
EXPIRED_PREFIX = config("EXPIRED_PREFIX")
EXPIRED_TTL = config("EXPIRED_TTL", cast=int)

MASTER_TTL = config("MASTER_TTL", cast=int)
NODES_TTL = config("NODES_TTL", cast=int)


CANE_SERVER_LISTEN_HOST = config("CANE_SERVER_LISTEN_HOST")
CANE_SERVER_LISTEN_PORT = config("CANE_SERVER_LISTEN_PORT", cast=int)

DEMO_APP_CANE_SERVER_HOST = config("DEMO_APP_CANE_SERVER_HOST")
DEMO_APP_HOST = config("DEMO_APP_HOST")
DEMO_APP_PORT = config("DEMO_APP_PORT", cast=int)

DEMO_APP_R_PREFIX_NODE = config("DEMO_APP_R_PREFIX_NODE")
DEMO_APP_R_PREFIX_MASTER = config("DEMO_APP_R_PREFIX_MASTER")