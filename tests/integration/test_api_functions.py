#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import scoring
import store
from tests.test_helpers import cases


class TestApiFunctionsSuite(unittest.TestCase):

    def setUp(self):
        storage_db = store.RedisLayer(host='localhost', port=6379)
        self.storage = store.Storage(storage=storage_db, attempts=10, attempts_timeout=0.01)
        self.storage.connect()
        scoring.gen_interests(self.storage, 0, 10)

    @cases([
        {'phone': '+1232938293824', 'email': '1test@test.com', 'birthday': '09.01.1986', 'gender': 1,
          'first_name': 'first', 'last_name': 'last', 'result': 5.0},
        {'phone': '+1232938293824', 'email': '2test@test.com', 'result': 3.0},
        {'phone': '+1232938293824', 'email': '3test@test.com', 'birthday': '09.01.1986', 'result': 3.0},
        {'phone': '+1232938293824', 'email': '4test@test.com', 'gender': 1, 'result': 3.0},
        {'phone': '+1232938293824', 'email': '5test@test.com', 'birthday': '09.01.1986', 'gender': 1, 'result': 4.5},
        {'phone': '+1232938293824', 'email': '6test@test.com', 'birthday': '09.01.1986', 'gender': 1,
         'first_name': 'last', 'result': 4.5},
        {'phone': '+1232938293824', 'email': '7test@test.com', 'birthday': '09.01.1986', 'gender': 1,
         'last_name': 'last', 'result': 4.5},
        {'phone': '+1232938293824', 'email': '8test@test.com', 'first_name': 'first', 'last_name': 'last', 'result': 3.5},
        {'phone': '+1232938293824', 'email': None, 'first_name': 'first', 'last_name': 'last', 'result': 2.0},
        {'phone': None, 'email': '8test@test.com', 'first_name': 'first', 'last_name': 'last', 'result': 2.0},
        {'phone': None, 'email': None, 'first_name': 'first', 'last_name': 'last', 'result': 0.5},
        {'phone': None, 'email': None, 'first_name': 'first', 'result': 0.0},
        {'phone': None, 'email': None, 'last_name': 'last', 'result': 0.0},
    ])
    def test_get_score(self, arguments):
        result = arguments['result']
        del arguments['result']
        score = scoring.get_score(self.storage, **arguments)
        self.assertEqual(result, score, "get_score({}) wrong result".format(arguments))

    def test_get_interests(self):
        for i in range(0, 10):
            res = scoring.get_interests(self.storage, i)
            self.assertTrue(isinstance(res, list) and len(res) == 2)


if __name__ == "__main__":
    unittest.main()
