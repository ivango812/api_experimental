#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import store


class TestStorageSuite(unittest.TestCase):

    def setUp(self):
        self.storage_db = store.RedisLayer(host='localhost', port=6379)
        self.storage = store.Storage(storage=self.storage_db, attempts=10, attempts_timeout=0.01)
        self.storage.connect()

    def test_Storage_set_get(self):
        self.storage.set('id', 42)
        self.assertEqual(self.storage.get('id'), "42")
        self.storage.set('iddqd', 'DeathMatch')
        self.assertEqual(self.storage.get('iddqd'), 'DeathMatch')

    def test_Storage_lost_connection_on_set(self):
        self.assertEqual(self.storage.attempts_decorator_counter, 0)
        self.assertEqual(self.storage.attempts_connect_counter, 0)
        del self.storage_db.connection
        self.storage.set('id', 42)
        self.assertEqual(self.storage.attempts_decorator_counter, 1)
        self.assertEqual(self.storage.attempts_connect_counter, 1)

    def test_Storage_lost_connection_on_get(self):
        self.assertEqual(self.storage.attempts_decorator_counter, 0)
        self.assertEqual(self.storage.attempts_connect_counter, 0)
        self.storage.set('id', 42)
        del self.storage_db.connection
        self.storage.get('id')
        self.assertEqual(self.storage.attempts_decorator_counter, 1)
        self.assertEqual(self.storage.attempts_connect_counter, 1)


if __name__ == "__main__":
    unittest.main()
