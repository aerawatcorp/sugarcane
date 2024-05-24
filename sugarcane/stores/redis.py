import redis
from stores import BaseStore


class RedisStore(BaseStore):
    def __init__(self, config):
        # Connect to Redis using config
        self.client = redis.Redis(**config)

    def store(self, data):
        try:
            # Attempt JSON serialization
            self.client.set(
                "data", self.serialize(data)
            )  # Replace 'data' with a desired key name
            return True
        except TypeError as e:
            # Handle non-JSON-serializable types
            print(f"Error serializing data for Redis: {e}")
            # Implement custom logic here (e.g., log error, raise exception)
            return False  # Or return False based on your error handling strategy
