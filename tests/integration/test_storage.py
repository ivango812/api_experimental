#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import store


class TestStorageSuite(unittest.TestCase):

    def setUp(self):
        pass

    def test_Storage_set_get(self):
        storage_db = store.RedisLayer(host='localhost', port=6379)
        storage = store.Storage(storage=storage_db, attempts=10, attempts_timeout=0.01)
        storage.connect()
        storage.set('id', 42)
        self.assertEqual(storage.get('id'), "42")
        storage.set('iddqd', 'DeathMatch')
        self.assertEqual(storage.get('iddqd'), 'DeathMatch')


if __name__ == "__main__":
    unittest.main()
