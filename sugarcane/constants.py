import os

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "content/")
DATA_NODES = ["post", "user", "food", "emoji", "people"]

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1

R_PREFIX = "cane:"
MASTER_KEY = "MASTER"
EXPIRED_PREFIX = "EXPIRED"
EXPIRED_TTL = 86400

MASTER_TTL = 10
NODES_TTL = 100

SERVICE_HOST = "http://localhost"
SERVICE_PORT = 8000
LISTEN_PORT = 8000
