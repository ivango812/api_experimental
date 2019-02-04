#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from .mock import StorageDBLayerMockMem, StorageDBLayerMockAttempsCounter
from store import Storage, RedisLayer


class TestStorageSuite(unittest.TestCase):

    def setUp(self):
        pass

    def test_store_set_get(self):
        redis = RedisLayer(host='localhost', port=6379)
        storage = Storage(storage=redis)
        storage.connect()
        key = 'key2'
        value = '1234567890'
        storage.set(key, value)
        self.assertEqual(storage.get(key), value, 'Error store.get({})'.format(key))

    def test_Storage_attempts_on_ConnectionError(self):
        storage_dblayer_mock = StorageDBLayerMockAttempsCounter()
        storage_dblayer_mock.mock_set_exception(ConnectionError)
        storage = Storage(storage=storage_dblayer_mock, attempts=10, attempts_timeout=0.01)

        self.assertEqual(storage_dblayer_mock.connect_count, 0)
        storage.connect()
        self.assertEqual(storage_dblayer_mock.connect_count, 10)

        self.assertEqual(storage_dblayer_mock.set_count, 0)
        storage.set('id', 1)
        self.assertEqual(storage_dblayer_mock.set_count, 10)

        self.assertEqual(storage_dblayer_mock.get_count, 0)
        value = storage.get('id')
        self.assertEqual(storage_dblayer_mock.get_count, 10)

    def test_Storage_attempts_on_TimeoutError(self):
        storage_dblayer_mock = StorageDBLayerMockAttempsCounter()
        storage_dblayer_mock.mock_set_exception(TimeoutError)
        storage = Storage(storage=storage_dblayer_mock, attempts=10, attempts_timeout=0.01)

        self.assertEqual(storage_dblayer_mock.connect_count, 0)
        storage.connect()
        self.assertEqual(storage_dblayer_mock.connect_count, 10)

        self.assertEqual(storage_dblayer_mock.set_count, 0)
        storage.set('id', 1)
        self.assertEqual(storage_dblayer_mock.set_count, 10)

        self.assertEqual(storage_dblayer_mock.get_count, 0)
        value = storage.get('id')
        self.assertEqual(storage_dblayer_mock.get_count, 10)

    def test_Storage_set_get(self):
        storage_dblayer_mock = StorageDBLayerMockMem()
        storage = Storage(storage=storage_dblayer_mock, attempts=10, attempts_timeout=0.01)
        storage.connect()
        storage.set('id', 42)
        self.assertEqual(storage_dblayer_mock.get('id'), 42)
        storage.set('iddqd', 'DeathMatch')
        self.assertEqual(storage_dblayer_mock.get('iddqd'), 'DeathMatch')


if __name__ == "__main__":
    unittest.main()
