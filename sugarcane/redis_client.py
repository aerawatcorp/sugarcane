import redis
from constants import REDIS_HOST, REDIS_PORT, REDIS_DB

# Redis connection 1
r1 = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# # Redis connection 2
# Later to be implemented as extended cache for cache avalance prevention
# r2 = redis.StrictRedis(host="localhost", port=6379, db=1)
