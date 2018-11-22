#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import functools
import api
from store import StoreRedis
import scoring
from datetime import datetime
from dateutil.relativedelta import relativedelta
import hashlib
import time


def cases(cases):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args):
            for case in cases:
                if not isinstance(case, tuple):
                    case = (case,)
                args_with_case = args + case
                func(*args_with_case)
        return wrapper
    return decorator


def cases_result(cases):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args):
            for case in cases:
                case_args = case[0]
                case_result = case[1]
                if not isinstance(case_args, tuple):
                    case_args = (case_args,)
                args_with_case = args + case_args + (case_result,)
                func(*args_with_case)
        return wrapper
    return decorator


class StoreMock(StoreRedis):

    storage = {}

    def __init__(self, *args, **kwargs):
        pass

    def set(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage[key] if key in self.storage else None

    def cache_set(self, key, value, expire=None):
        self.set(key, value)

    def cache_get(self, key):
        return self.get(key)


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store_mock = StoreMock()
        scoring.gen_interests(self.store_mock, 0, 10)
        self.store = StoreRedis(host='localhost', port=6379)

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store_mock)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(str(datetime.now().strftime("%Y%m%d%H")
                                                  + api.ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            msg = str(request.get("account", "") + request.get("login", "") + api.SALT).encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

# =================
# Unit test section
# =================

    @cases_result([
        [{'phone': '+1232938293824', 'email': '1test@test.com', 'birthday': '09.01.1986', 'gender': 1,
          'first_name': 'first', 'last_name': 'last'}, 5.0],
        [{'phone': '+1232938293824', 'email': '2test@test.com'}, 3.0],
        [{'phone': '+1232938293824', 'email': '3test@test.com', 'birthday': '09.01.1986'}, 3.0],
        [{'phone': '+1232938293824', 'email': '4test@test.com', 'gender': 1}, 3.0],
        [{'phone': '+1232938293824', 'email': '5test@test.com', 'birthday': '09.01.1986', 'gender': 1}, 4.5],
        [{'phone': '+1232938293824', 'email': '6test@test.com', 'birthday': '09.01.1986', 'gender': 1,
          'first_name': 'last'}, 4.5],
        [{'phone': '+1232938293824', 'email': '7test@test.com', 'birthday': '09.01.1986', 'gender': 1,
          'last_name': 'last'}, 4.5],
        [{'phone': '+1232938293824', 'email': '8test@test.com', 'first_name': 'first', 'last_name': 'last'}, 3.5],
        [{'phone': '+1232938293824', 'email': None, 'first_name': 'first', 'last_name': 'last'}, 2.0],
        [{'phone': None, 'email': '8test@test.com', 'first_name': 'first', 'last_name': 'last'}, 2.0],
        [{'phone': None, 'email': None, 'first_name': 'first', 'last_name': 'last'}, 0.5],
        [{'phone': None, 'email': None, 'first_name': 'first'}, 0.0],
        [{'phone': None, 'email': None, 'last_name': 'last'}, 0.0],

    ])
    def test_get_score(self, arguments, result):
        score = scoring.get_score(self.store_mock, **arguments)
        self.assertEqual(result, score, "get_score({}) wrong result".format(arguments))

    @cases([
        {'phone': '71234567890', 'email': '1test@test.com', 'gender': 1, 'first_name': 'first', 'last_name': 'last',
         'birthday': datetime.strftime(datetime.now() - relativedelta(years=+70), '%d.%m.%Y'),
         },
        {'phone': 71234567890, 'email': '1test.dsfdsfdsf@test.com', 'gender': 2, 'first_name': 'first2',
         'last_name': 'last2',
         'birthday': datetime.strftime(datetime.now(), '%d.%m.%Y'),
         },
    ])
    def test_OnlineScoreRequest_valid_fields(self, arguments):
        request = api.OnlineScoreRequest(arguments)
        request.validate()
        self.assertEqual(str(arguments['phone']), request.phone)
        self.assertEqual(arguments['email'], request.email)
        self.assertEqual(arguments['birthday'], request.birthday)
        self.assertEqual(arguments['gender'], request.gender)
        self.assertEqual(arguments['first_name'], request.first_name)
        self.assertEqual(arguments['last_name'], request.last_name)
        self.assertFalse(request.errors)
        self.assertTrue(request.is_valid(), 'is_valid()')

    @cases([
        {'phone': '10987654321', 'birthday': '09.01.1986', 'gender': 1, 'first_name': 'first', 'last_name': 'last'},
    ])
    def test_OnlineScoreRequest_AttributeError(self, arguments):
        request = api.OnlineScoreRequest(arguments)
        request.validate()
        # self.assertRaises(AttributeError, getattr, request, 'phone')
        with self.assertRaises(AttributeError): request.phone

    @cases([
        {'phone': '10987654321'},
        {'phone': '+70987654321'},
        {'phone': '7(098)765-43-21'},
    ])
    def test_OnlineScoreRequest_validate_phone(self, arguments):
        request = api.OnlineScoreRequest(arguments)
        request.validate()
        err = request.errors
        self.assertEqual(1, len(err))
        self.assertTrue(err['phone'])

    @cases([
        {'gender': 1, 'birthday': 9011986},
        {'gender': 1, 'birthday': '01.13.2000'},
        {'gender': 1, 'birthday': datetime.strftime(datetime.now() - relativedelta(years=+70, days=+1), '%d.%m.%Y')},
        {'gender': 1, 'birthday': datetime.strftime(datetime.now() - relativedelta(years=+170), '%d.%m.%Y')},
    ])
    def test_OnlineScoreRequest_validate_birthday(self, arguments):
        request = api.OnlineScoreRequest(arguments)
        request.validate()
        err = request.errors
        self.assertEqual(1, len(err), "errors: {}, arguments={}".format(err, arguments))
        self.assertTrue(err['birthday'])

    @cases([
        {'email': 'email(at)domain.com'},
    ])
    def test_OnlineScoreRequest_validate_email(self, arguments):
        request = api.OnlineScoreRequest(arguments)
        request.validate()
        err = request.errors
        self.assertEqual(1, len(err))
        self.assertTrue(err['email'])

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

    @cases([
        {'client_ids': [1, 2, 3], 'date': '01.01.2001'},
        {'client_ids': [0, 2, 3, 5, 6, 7], 'date': '31.12.1900'},
    ])
    def test_ClientsInterestsRequest_valid_fields(self, arguments):
        request = api.ClientsInterestsRequest(arguments)
        request.validate()
        self.assertEqual(arguments['client_ids'], request.client_ids)
        self.assertEqual(arguments['date'], request.date)
        self.assertFalse(request.errors)
        self.assertTrue(request.is_valid(), 'is_valid()')

    @cases([
        {'client_ids': [1, 2, 3, 'a'], 'date': '01.01.2001'},
        {'client_ids': 1, 'date': '01.12.1900'},
    ])
    def test_ClientsInterestsRequest_validate_client_ids(self, arguments):
        request = api.ClientsInterestsRequest(arguments)
        request.validate()
        err = request.errors
        self.assertEqual(1, len(err))
        self.assertTrue(err['client_ids'])

    @cases([
        {'client_ids': [1, 2, 3], 'date': '32.01.2001'},
        {'client_ids': [1, 2, 3], 'date': 1012001},
    ])
    def test_ClientsInterestsRequest_validate_date(self, arguments):
        request = api.ClientsInterestsRequest(arguments)
        request.validate()
        err = request.errors
        self.assertEqual(1, len(err))
        self.assertTrue(err['date'])

    def test_get_interests(self):
        for i in range(0, 10):
            res = scoring.get_interests(self.store_mock, i)
            self.assertTrue(isinstance(res, list) and len(res) == 2)

    @cases([
        {'key': 'key2', 'value': '1234567890'},
        # {'key': 'key1', 'value': 1234567890}, # cache saves only str
        # {'key': 'key3', 'value': [1, 2, 3]}, # cache saves only str
    ])
    def test_store_cache(self, arguments):
        key = arguments['key']
        value = arguments['value']
        self.store.cache_set(key, value, 3)
        time.sleep(1)
        self.assertEqual(self.store.cache_get(key), value, 'Cache is not saved for value {}({})!'.format(type(value), value))
        time.sleep(2)
        self.assertEqual(self.store.cache_get(key), None, 'Cache is not expired!')

    @cases([
        {'key': 'key2', 'value': '1234567890'},
        # {'key': 'key1', 'value': 1234567890}, # cache saves only str
        # {'key': 'key3', 'value': [1, 2, 3]}, # cache saves only str
    ])
    def test_store_set_get(self, arguments):
        key = arguments['key']
        value = arguments['value']
        self.store.set(key, value)
        self.assertEqual(self.store.get(key), value, 'Error store.get({})'.format(key))


# ========================
# Functional tests section
# ========================

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, str) for i in v)
                        for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


if __name__ == "__main__":
    unittest.main()
