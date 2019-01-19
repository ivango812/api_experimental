import redis
import logging


class RedisLayer:

    connection = None

    def __init__(self, host='localhost', port=6379, socket_timeout=2, socket_connect_timeout=5, attempts=5):
        self.db = 0
        self.attempts = attempts
        self.host = host
        self.port = port
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout

    def connect(self):
        self.connection = redis.StrictRedis(host=self.host, port=self.port, db=self.db,
                                            decode_responses=True,
                                            socket_timeout=self.socket_timeout,
                                            socket_connect_timeout=self.socket_connect_timeout)
        self.connection.flushdb()

    def get(self, key):
        return self.connection.get(key)

    def set(self, key, value, expire=None):
        self.connection.set(key, value, expire)


class Storage:

    storage = None
    # red = None

    def __init__(self, storage=storage, attempts=5):
        self.attempts = attempts
        self.storage = storage

    def connect(self):
        for i in range(self.attempts):
            try:
                self.storage.connect()
            except Exception as e:
                if i < self.attempts:
                    logging.info(e)
                else:
                    raise

    def try_with_repeats(self, func, arguments):
        for i in range(self.attempts):
            try:
                res = func(*arguments)
                return res
            except (TimeoutError, ConnectionError):
                self.connect()

    def set(self, key, value):
        self.try_with_repeats(self.storage.set, [key, value])

    def get(self, key):
        return self.try_with_repeats(self.storage.get, [key])

    def cache_set(self, key, value, expire=None):
        self.try_with_repeats(self.storage.set, [key, value, expire])

    def cache_get(self, key):
        return self.get(key)

