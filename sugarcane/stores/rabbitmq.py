import pika
from stores import BaseStore

"""
TODO: 
This store is an example of how to store data in RabbitMQ.
"""


class RabbitmqStore(BaseStore):
    def __init__(self, config):
        # Get RabbitMQ connection details from config
        credentials = pika.PlainCredentials(config["username"], config["password"])
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config["host"], credentials=credentials)
        )
        self.channel = self.connection.channel()

        # Define exchange and queue (adjust as needed)
        self.exchange_name = "data_exchange"
        self.queue_name = "data_queue"
        self.channel.queue_declare(queue=self.queue_name)

    def store(self, data):
        # Publish data to RabbitMQ queue
        self.channel.basic_publish(
            exchange=self.exchange_name, routing_key=self.queue_name, body=data
        )
        return True  # Return success or failure (consider error handling)

    def close(self):  # Optional: Close connection on application shutdown
        self.connection.close()
