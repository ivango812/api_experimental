#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from ..test_helpers import cases
import api
from store import Storage, RedisLayer
import scoring
from datetime import datetime
from dateutil.relativedelta import relativedelta
import hashlib
import time


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
        # self.memstorage[key] = value
        self.set_count += 1
        raise self.exception

    def get(self, key):
        self.get_count += 1
        raise self.exception
        # return self.memstorage[key] if key in self.memstorage else None

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


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.storage_mock = StorageDBLayerMockMem()
        scoring.gen_interests(self.storage_mock, 0, 10)
        # redis = RedisLayer(host='localhost', port=6379)
        self.storage = Storage(storage=self.storage_mock)
        self.storage.connect()

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(str(datetime.now().strftime("%Y%m%d%H")
                                                  + api.ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            msg = str(request.get("account", "") + request.get("login", "") + api.SALT).encode('utf-8')
            request["token"] = hashlib.sha512(msg).hexdigest()

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
        score = scoring.get_score(self.storage_mock, **arguments)
        self.assertEqual(result, score, "get_score({}) wrong result".format(arguments))

    def test_BaseField(self):
        base_field = api.BaseField()
        self.assertFalse(base_field.nullable)
        self.assertFalse(base_field.required)
        self.assertRaises(api.ValidationError, base_field.validate, None)
        self.assertRaises(api.ValidationError, base_field.validate, '')
        self.assertRaises(api.ValidationError, base_field.validate, [])
        self.assertRaises(api.ValidationError, base_field.validate, {})
        self.assertRaises(api.ValidationError, base_field.validate, ())

        self.assertEqual(base_field.validate_type('test'), 'test')
        self.assertEqual(base_field.clean('test'), 'test')

        base_field = api.BaseField(required=True, nullable=True)
        self.assertTrue(base_field.nullable)
        self.assertTrue(base_field.required)
        base_field.validate_type(None)
        base_field.validate_type([])
        base_field.validate_type({})
        base_field.validate_type(())
        base_field.validate_type('')

    def test_CharField(self):
        char_field = api.CharField()
        self.assertEqual(char_field.validate_type('test'), 'test')
        self.assertRaises(TypeError, char_field.validate_type, True)
        self.assertRaises(TypeError, char_field.validate_type, 1)
        self.assertRaises(TypeError, char_field.validate_type, 1.1)
        self.assertRaises(TypeError, char_field.validate_type, [])
        self.assertRaises(TypeError, char_field.validate_type, {})
        self.assertRaises(TypeError, char_field.validate_type, ())

    def test_ArgumentsField(self):
        arguments_field = api.ArgumentsField()
        test_dict = {'a': 1, 'b': 2, 'c': 3}
        self.assertDictEqual(arguments_field.validate_type(test_dict), test_dict)
        self.assertRaises(TypeError, arguments_field.validate_type, True)
        self.assertRaises(TypeError, arguments_field.validate_type, 1)
        self.assertRaises(TypeError, arguments_field.validate_type, 1.1)
        self.assertRaises(TypeError, arguments_field.validate_type, [])
        self.assertRaises(TypeError, arguments_field.validate_type, 'test')
        self.assertRaises(TypeError, arguments_field.validate_type, ())

    def test_EmailField(self):
        email_field = api.EmailField()
        self.assertIsInstance(email_field, api.CharField)
        email_field.validate_content('fierstname.lastname@sub.domain.com')
        self.assertRaises(api.ValidationError, email_field.validate_content, 'name domain.com')
        self.assertRaises(api.ValidationError, email_field.validate_content, 'name(at)domain.com')
        self.assertRaises(api.ValidationError, email_field.validate_content, 'name.domain.com')

    def test_PhoneField(self):
        phone_field = api.PhoneField()
        self.assertEqual(phone_field.validate_type('+1234567890'), '+1234567890')
        self.assertEqual(phone_field.validate_type('1234567890'), '1234567890')
        self.assertEqual(phone_field.validate_type(1234567890), '1234567890')
        self.assertRaises(TypeError, phone_field.validate_type, 1.1)
        self.assertRaises(TypeError, phone_field.validate_type, [])
        self.assertRaises(TypeError, phone_field.validate_type, {})
        self.assertRaises(TypeError, phone_field.validate_type, ())

    def test_FateField(self):
        date_field = api.DateField()
        self.assertIsInstance(date_field, api.CharField)
        self.assertEqual(date_field.validate_type('01.01.0001'), '01.01.0001')
        self.assertEqual(date_field.validate_type('01.01.1900'), '01.01.1900')
        self.assertEqual(date_field.validate_type('31.01.2020'), '31.01.2020')
        self.assertEqual(date_field.validate_type('29.02.2020'), '29.02.2020')
        self.assertEqual(date_field.validate_type('1.1.1900'), '1.1.1900')
        self.assertEqual(date_field.validate_type('1.1.0001'), '1.1.0001')

        self.assertRaises(api.ValidationError, date_field.validate_type, '29.02.2019')
        self.assertRaises(api.ValidationError, date_field.validate_type, '31.02.2020')
        self.assertRaises(api.ValidationError, date_field.validate_type, ' 01.01.1900')

    def get_date_for_age(self, age_years, age_months=0, age_days=0):
        return datetime.strftime(datetime.now() - relativedelta(years=+age_years, months=+age_months, days=+age_days), '%d.%m.%Y')


    def test_BirthDayField(self):
        birthday_field = api.BirthDayField()
        self.assertIsInstance(birthday_field, api.DateField)
        birthday_field.validate_content(self.get_date_for_age(age_years=70))
        birthday_field.validate_content(self.get_date_for_age(age_years=1))
        birthday_field.validate_content('01.01.2030')
        self.assertRaises(api.ValidationError, birthday_field.validate_content,
                                               self.get_date_for_age(age_years=70, age_days=1))
        self.assertRaises(api.ValidationError, birthday_field.validate_content,
                                               self.get_date_for_age(age_years=170, age_days=1))

    def test_GenderField(self):
        gender_field = api.GenderField()
        self.assertEqual(gender_field.validate_type(0), 0)
        self.assertRaises(TypeError, gender_field.validate_type, 0.0)
        self.assertRaises(TypeError, gender_field.validate_type, '0')
        self.assertRaises(TypeError, gender_field.validate_type, [])
        self.assertRaises(TypeError, gender_field.validate_type, {})
        self.assertRaises(TypeError, gender_field.validate_type, ())

        gender_field.validate_content(0)
        gender_field.validate_content(1)
        gender_field.validate_content(2)
        self.assertRaises(api.ValidationError, gender_field.validate_content, -1)
        self.assertRaises(api.ValidationError, gender_field.validate_content, 3)
        self.assertRaises(TypeError, gender_field.validate_content, 1.0001)
        self.assertRaises(TypeError, gender_field.validate_content, '0')
        self.assertRaises(TypeError, gender_field.validate_content, [])
        self.assertRaises(TypeError, gender_field.validate_content, {})
        self.assertRaises(TypeError, gender_field.validate_content, ())

    def test_ClientIDsField(self):
        clientids_field = api.ClientIDsField()
        self.assertListEqual(clientids_field.validate_type([]), [])
        self.assertListEqual(clientids_field.validate_type([0, 1, 2]), [0, 1, 2])
        self.assertRaises(TypeError, clientids_field.validate_type, [0, 1, '2'])
        self.assertRaises(TypeError, clientids_field.validate_type, [0, 1, 2.0])
        clientids_field.validate_content([0, 1, 2, 100000])
        self.assertRaises(api.ValidationError, clientids_field.validate_content, [-1, 0])

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
        self.assertTrue(request.is_valid())

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
            res = scoring.get_interests(self.storage_mock, i)
            self.assertTrue(isinstance(res, list) and len(res) == 2)

    # @cases([
    #     {'key': 'key2', 'value': '1234567890'},
    #     # {'key': 'key1', 'value': 1234567890}, # cache saves only str
    #     # {'key': 'key3', 'value': [1, 2, 3]}, # cache saves only str
    # ])
    # def test_store_cache(self, arguments):
    #     key = arguments['key']
    #     value = arguments['value']
    #     self.storage.cache_set(key, value, 3)
    #     time.sleep(1)
    #     self.assertEqual(self.storage.cache_get(key), value, 'Cache is not saved for value {}({})!'.format(type(value), value))
    #     time.sleep(2)
    #     self.assertEqual(self.storage.cache_get(key), None, 'Cache is not expired!')

    @cases([
        {'key': 'key2', 'value': '1234567890'},
        # {'key': 'key1', 'value': 1234567890}, # cache saves only str
        # {'key': 'key3', 'value': [1, 2, 3]}, # cache saves only str
    ])
    def test_store_set_get(self, arguments):
        key = arguments['key']
        value = arguments['value']
        self.storage.set(key, value)
        self.assertEqual(self.storage.get(key), value, 'Error store.get({})'.format(key))

    def test_Storage_attempts_on_ConnectionError(self):
        storage_dblayer_mock = StorageDBLayerMockAttempsCounter()
        storage_dblayer_mock.mock_set_exception(ConnectionError)
        storage = Storage(storage=storage_dblayer_mock, attempts=10)

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
        storage = Storage(storage=storage_dblayer_mock, attempts=10)

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
        storage = Storage(storage=storage_dblayer_mock, attempts=10)
        storage.connect()
        storage.set('id', 42)
        self.assertEqual(storage_dblayer_mock.get('id'), 42)
        storage.set('iddqd', 'DeathMatch')
        self.assertEqual(storage_dblayer_mock.get('iddqd'), 'DeathMatch')



if __name__ == "__main__":
    unittest.main()
