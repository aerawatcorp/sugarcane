import os

from decouple import AutoConfig

config = AutoConfig(search_path="/app")

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "../content/datadir/")
MASTER_SCHEMA_PATH = os.path.join(CONTENT_ROOT, "master.json")

REDIS_HOST_CANE = config("REDIS_HOST_CANE", default="redis.sugarcane.svc.cluster.local")
REDIS_PORT_CANE = config("REDIS_PORT_CANE", default=6379)
REDIS_DB_CANE = config("REDIS_DB_CANE")

CANE_SERVER_LISTEN_HOST = config("CANE_SERVER_LISTEN_HOST")
CANE_SERVER_LISTEN_PORT = config("CANE_SERVER_LISTEN_PORT", cast=int)


REDIS_HOST_DEMO = config("REDIS_HOST_DEMO", default="redis")
REDIS_PORT_DEMO = config("REDIS_PORT_DEMO", default=6379)
REDIS_DB_DEMO = config("REDIS_DB_DEMO")

R_PREFIX = config("R_PREFIX")
MASTER_KEY = config("MASTER_KEY")
MASTER_KEY_VERBOSED = f"{MASTER_KEY}-v"

EXPIRED_PREFIX = config("EXPIRED_PREFIX")
EXPIRED_TTL = config("EXPIRED_TTL", cast=int)

MASTER_TTL = config("MASTER_TTL", cast=int)

MASTER_API_URL = config("MASTER_API_URL", default="")
NODE_API_URL = config("NODE_API_URL", default="")

JAGGERY_BASE_URL = config("JAGGERY_BASE_URL", default="")
MASTER_JAGGERY_API_URL = config("MASTER_JAGGERY_API_URL", default="")
NODE_JAGGERY_API_URL = config("NODE_JAGGERY_API_URL", default="")

CANE_SERVER_LISTEN_HOST = config("CANE_SERVER_LISTEN_HOST")
CANE_SERVER_LISTEN_PORT = config("CANE_SERVER_LISTEN_PORT", cast=int)

DEMO_APP_CANE_SERVER_HOST = config("DEMO_APP_CANE_SERVER_HOST")
DEMO_APP_HOST = config("DEMO_APP_HOST")
DEMO_APP_PORT = config("DEMO_APP_PORT", cast=int)

DEMO_APP_R_PREFIX_NODE = config("DEMO_APP_R_PREFIX_NODE")
DEMO_APP_R_PREFIX_MASTER = config("DEMO_APP_R_PREFIX_MASTER")

REQUEST_TIMEOUT = config("REQUEST_TIMEOUT", default=60, cast=int)
