import logging
import redis
import time

logging.basicConfig(filename='test.log', level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')


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


def try_with_repeats(func):
    def wrapper(self, *args):
        for i in range(self.attempts):
            try:
                return func(self, *args)
            except (TimeoutError, ConnectionError, AttributeError) as e:
                self.attempts_decorator_counter += 1
                logging.info('Error {}() call, trying reconnect: {} ...'.format(func, i + 1))
                self.connect()
                self.attempts_connect_counter += 1
    return wrapper


class Storage:

    storage = None
    attempts_connect_counter = 0
    attempts_decorator_counter = 0
    # red = None

    def __init__(self, storage=storage, attempts=5, attempts_timeout=1):
        self.attempts = attempts
        self.storage = storage
        self.attempts_timeout = attempts_timeout

    def connect(self):
        for i in range(self.attempts):
            try:
                self.storage.connect()
            except Exception as e:
                if i < self.attempts:
                    self.attempts_connect_counter += 1
                    logging.info('Connection retry: {}'.format(i + 1))
                    time.sleep(self.attempts_timeout)
                else:
                    raise

    @try_with_repeats
    def set(self, key, value):
        self.storage.set(key, value)

    @try_with_repeats
    def get(self, key):
        return self.storage.get(key)

    def cache_set(self, key, value, expire=None):
        self.storage.set(key, value, expire)

    def cache_get(self, key):
        return self.get(key)

