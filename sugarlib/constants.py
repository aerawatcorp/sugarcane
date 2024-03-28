import os

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "../content/datadir/")
DATA_NODES = ["post", "user", "food", "emoji", "people"]

REDIS_HOST_CANE = "redis"
REDIS_PORT_CANE = 6379
REDIS_DB_CANE = 1

REDIS_HOST_DEMO = "redis"
REDIS_PORT_DEMO = 6379
REDIS_DB_DEMO = 2

R_PREFIX = "cane:"
MASTER_KEY = "MASTER"
EXPIRED_PREFIX = "EXPIRED"
EXPIRED_TTL = 86400

MASTER_TTL = 10
NODES_TTL = 100

CANE_SERVER_HOST = "http://localhost"
CSNE_SERVER_PORT = 8000

DEMO_APP_HOST = "http://localhost"
DEMO_APP_PORT = 5000