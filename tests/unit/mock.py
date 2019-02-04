from store import RedisLayer


class StorageDBLayerMockAttempsCounter(RedisLayer):

    memstorage = {}
    connect_count = 0
    set_count = 0
    get_count = 0
    exception = ConnectionError

    def __init__(self, *args, **kwargs):
        pass

    def mock_reset_counters(self):
        self.connect_count = 0
        self.set_count = 0
        self.get_count = 0

    def mock_set_exception(self, exception=ConnectionError):
        if exception in [ConnectionError, TimeoutError]:
            self.exception = exception
        else:
            raise TypeError('Wrong exception type passed!')

    def connect(self):
        self.connect_count += 1
        raise self.exception

    def set(self, key, value, expire=None):
        self.set_count += 1
        raise self.exception

    def get(self, key):
        self.get_count += 1
        raise self.exception

    def cache_set(self, key, value, expire=None):
        self.set(key, value)

    def cache_get(self, key):
        return self.get(key)


class StorageDBLayerMockMem(RedisLayer):

    memstorage = {}

    def __init__(self, *args, **kwargs):
        pass

    def connect(self):
        pass

    def set(self, key, value, expire=None):
        self.memstorage[key] = value

    def get(self, key):
        return self.memstorage[key] if key in self.memstorage else None

    def cache_set(self, key, value, expire=None):
        self.set(key, value)

    def cache_get(self, key):
        return self.get(key)
