import pymemcache
from stores import BaseStore


class MemcachedStore(BaseStore):
    def __init__(self, config):
        # Get Memcached server details from config
        self.client = pymemcache.Client((config["host"], config["port"]))

    def store(self, data):
        # Set data in Memcached with an expiry time (adjust as needed)
        self.client.set("data", self.serialize(data), expire=3600)  # 1 hour
        return True  # Return success or failure (consider error handling)
