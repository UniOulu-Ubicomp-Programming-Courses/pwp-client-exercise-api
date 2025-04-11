import json
import random
import ssl
from flask import current_app
import pika
import redis


class RedisBackend(object):

    def __init__(self):
        self.db = current_app.config["REDIS_DB"]
        self.host = current_app.config["REDIS_HOST"]
        self.port = current_app.config.get("REDIS_PORT", 6379)
        #self.passwd = passwd

    def get_client(self):
        return redis.Redis(
            host=self.host,
            #ssl=True,
            #password=self.passwd,
            db=self.db
        )

    def save(self, key, content, timeout=None):
        client = self.get_client()
        if timeout is not None:
            client.setex(key, timeout, json.dumps(content))
        else:
            client.set(key, json.dumps(content))

    def load(self, key):
        client = self.get_client()
        return json.loads(client.get(key))


class RabbitBackend(object):

    def __init__(self):
        self.host = current_app.config["RABBITMQ_HOST"]
        self.port = current_app.config.get("RABBITMQ_PORT", 5671)
        self.user = current_app.config["RABBITMQ_USER"]
        self.passwd = current_app.config["RABBITMQ_PASS"]
        self.credentials = pika.PlainCredentials(self.user, self.passwd)

    @property
    def uri_template(self):
        return f"amqps://{{username}}:{{password}}@{self.host}:{self.port}/{{vhost}}"

    @property
    def conn_template(self):
        return {
            "host": self.host,
            "port": self.port,
            "virtual_host": "{group}-vhost"
        }

    def get_connection(self):
        context = ssl.create_default_context(cafile=current_app.config["CA_CERT"])
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(
            current_app.config["CLIENT_CERT"],
            current_app.config["CLIENT_KEY"],
        )
        return pika.BlockingConnection(pika.ConnectionParameters(
            self.host,
            self.port,
            "/",
            self.credentials,
            ssl_options=pika.SSLOptions(context)
        ))

    def send_task(self, body, token):
        connection = self.get_connection()
        channel = connection.channel()
        channel.queue_declare(
            queue=f"delay-{token}",
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "tasks",
                "x-message-ttl": random.randint(5000, 1000 * 3600),
            }
        )
        channel.basic_publish(
            exchange="",
            routing_key=f"delay-{token}",
            body=json.dumps(body),
        )
        connection.close()
