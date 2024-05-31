"""
The demo application will use Redis as a cache to store the results of the API calls.
"""

import redis

from sugarlib.constants import REDIS_HOST_CANE, REDIS_PORT_CANE, REDIS_DB_CANE
from sugarlib.constants import REDIS_HOST_DEMO, REDIS_PORT_DEMO, REDIS_DB_DEMO

# Redis connection 1
r1_cane = redis.StrictRedis(
    host=REDIS_HOST_CANE, port=REDIS_PORT_CANE, db=REDIS_DB_CANE
)
r2_demo = redis.StrictRedis(
    host=REDIS_HOST_DEMO, port=REDIS_PORT_DEMO, db=REDIS_DB_DEMO
)
