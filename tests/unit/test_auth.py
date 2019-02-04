#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import hashlib
import unittest

import api
from tests.test_helpers import cases


class TestAuthSuite(unittest.TestCase):

    def setUp(self):
        pass

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(str(datetime.now().strftime("%Y%m%d%H")
                                                  + api.ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            msg = str(request.get("account", "") + request.get("login", "") + api.SALT).encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()

    @cases([
        {'account': 'horns&hoofs', 'login': 'admin', 'method': 'clients_interests', 'arguments': {'a': 1, 'b': 2}},
    ])
    def test_ok_auth_admin(self, arguments):
        self.set_valid_auth(arguments)
        request = api.MethodRequest(arguments)
        request.validate()
        self.assertTrue(request.is_valid())
        self.assertFalse(request.errors)
        self.assertTrue(api.check_auth(request), "errors={}".format(request.errors))
        self.assertTrue(request.is_admin)

    @cases([
        {'account': 'horns&hoofs', 'login': 'admin', 'method': 'clients_interests', 'arguments': {'a': 1, 'b': 2}},
    ])
    def test_invalid_auth_admin(self, arguments):
        self.set_valid_auth(arguments)
        arguments['login'] = 'admin1'
        request = api.MethodRequest(arguments)
        request.validate()
        self.assertTrue(request.is_valid())
        self.assertFalse(request.errors)
        self.assertFalse(api.check_auth(request), "errors={}".format(request.errors))
        self.assertFalse(request.is_admin)

    @cases([
        {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'clients_interests', 'arguments': {'a': 1, 'b': 2}},
    ])
    def test_ok_auth(self, arguments):
        self.set_valid_auth(arguments)
        request = api.MethodRequest(arguments)
        request.validate()
        self.assertTrue(request.is_valid())
        self.assertFalse(request.errors)
        self.assertTrue(api.check_auth(request))
        self.assertFalse(request.is_admin)

    @cases([
        {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'clients_interests', 'arguments': {'a': 1, 'b': 2}},
    ])
    def test_invalid_auth(self, arguments):
        self.set_valid_auth(arguments)
        arguments['login'] = 'f&f'
        request = api.MethodRequest(arguments)
        request.validate()
        self.assertTrue(request.is_valid())
        self.assertFalse(request.errors)
        self.assertFalse(api.check_auth(request))
        self.assertFalse(request.is_admin)


if __name__ == "__main__":
    unittest.main()
