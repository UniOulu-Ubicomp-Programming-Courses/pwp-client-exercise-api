import json
import random
import ssl
import pika
import redis


class RedisBackend(object):

    def __init__(self, uri_string, passwd):
        address, self.db =  uri_string.rsplit("/", 1)
        host, port = address.rsplit(":", 1)
        self.host = host
        self.port = int(port)
        self.passwd = passwd

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

    def __init__(self, broker, user, passwd):
        host, port = broker.split(":")
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
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
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
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
                "x-message-ttl": random.randint(5000, 5000 * 3600 * 3600),
            }
        )
        channel.basic_publish(
            exchange="",
            routing_key=f"delay-{token}",
            body=json.dumps(body),
        )
        connection.close()






