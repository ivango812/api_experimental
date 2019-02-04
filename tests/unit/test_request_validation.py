#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import unittest

import api
from tests.test_helpers import cases


class TestRequestValidationSuite(unittest.TestCase):

    def setUp(self):
        pass

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
        with self.assertRaises(AttributeError): request.phone

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


if __name__ == "__main__":
    unittest.main()
