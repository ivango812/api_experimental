#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import unittest

import api
from tests.test_helpers import cases


class TestFieldValidationSuite(unittest.TestCase):

    def setUp(self):
        pass

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


if __name__ == "__main__":
    unittest.main()
