#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import unittest

import api
from tests.test_helpers import cases


class TestFieldDescriptorsSuite(unittest.TestCase):

    def setUp(self):
        pass

    def test_BaseField_validate_type(self):
        base_field = api.BaseField()
        self.assertEqual(base_field.validate_type('test'), 'test')

    def test_BaseField_clean(self):
        base_field = api.BaseField()
        self.assertEqual(base_field.clean('test'), 'test')

    def test_BaseField_required(self):
        base_field = api.BaseField()
        self.assertFalse(base_field.required)

        base_field = api.BaseField(required=True, nullable=True)
        self.assertTrue(base_field.required)

    def test_BaseField_nullable(self):
        base_field = api.BaseField()
        self.assertFalse(base_field.nullable)

        base_field = api.BaseField(required=True, nullable=True)
        self.assertTrue(base_field.nullable)

    @cases([
        {'value': None},
        {'value': ''},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_BaseField_validation_not_required_not_nullable(self, arguments):
        base_field = api.BaseField()
        self.assertRaises(api.ValidationError, base_field.validate, arguments['value'])

    @cases([
        {'value': None},
        {'value': ''},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_BaseField_validation_required_nullable(self, arguments):
        base_field = api.BaseField(required=True, nullable=True)
        base_field.validate_type(arguments['value'])

    def test_CharField(self):
        char_field = api.CharField()
        self.assertEqual(char_field.validate_type('test'), 'test')

    @cases([
        {'value': True},
        {'value': 1},
        {'value': 1.1},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_CharField_validate_type(self, arguments):
        char_field = api.CharField()
        self.assertRaises(TypeError, char_field.validate_type, arguments['value'])

    def test_ArgumentsField(self):
        arguments_field = api.ArgumentsField()
        test_dict = {'a': 1, 'b': 2, 'c': 3}
        self.assertDictEqual(arguments_field.validate_type(test_dict), test_dict)

    @cases([
        {'value': True},
        {'value': 1},
        {'value': 1.1},
        {'value': []},
        {'value': 'test'},
        {'value': ()},
    ])
    def test_ArgumentsField_validate_type(self, arguments):
        arguments_field = api.ArgumentsField()
        self.assertRaises(TypeError, arguments_field.validate_type, arguments['value'])

    def test_EmailField(self):
        email_field = api.EmailField()
        self.assertIsInstance(email_field, api.CharField)
        email_field.validate_content('fierstname.lastname@sub.domain.com')

    @cases([
        {'value': 'name domain.com'},
        {'value': 'name(at)domain.com'},
    ])
    def test_EmailField_validate_content_error(self, arguments):
        email_field = api.EmailField()
        self.assertRaises(api.ValidationError, email_field.validate_content, arguments['value'])

    @cases([
        {'value': '+1234567890', 'result': '+1234567890'},
        {'value': '1234567890', 'result': '1234567890'},
        {'value': 1234567890, 'result': '1234567890'},
    ])
    def test_PhoneField_validate(self, arguments):
        phone_field = api.PhoneField()
        self.assertEqual(phone_field.validate_type(arguments['value']), arguments['result'])

    @cases([
        {'value': 1.1},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_PhoneField_validate_TypeError(self, arguments):
        phone_field = api.PhoneField()
        self.assertRaises(TypeError, phone_field.validate_type, arguments['value'])

    def test_DateField(self):
        date_field = api.DateField()
        self.assertIsInstance(date_field, api.CharField)

    @cases([
        {'value': '01.01.0001'},
        {'value': '01.01.1900'},
        {'value': '31.01.2020'},
        {'value': '29.02.2020'},
        {'value': '1.1.1900'},
        {'value': '1.1.0001'},
    ])
    def test_DateField_validate_type(self, arguments):
        date_field = api.DateField()
        self.assertEqual(date_field.validate_type(arguments['value']), arguments['value'])

    @cases([
        {'value': '29.02.2019'},
        {'value': '31.02.2020'},
        {'value': ' 01.01.1900'},
    ])
    def test_DateField_validate_type_error(self, arguments):
        date_field = api.DateField()
        self.assertRaises(api.ValidationError, date_field.validate_type, arguments['value'])

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

    def test_GenderField_validate_type(self):
        gender_field = api.GenderField()
        self.assertEqual(gender_field.validate_type(0), 0)

    @cases([
        {'value': 0.0},
        {'value': '0'},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_GenderField_validate_type_error(self, arguments):
        gender_field = api.GenderField()
        self.assertRaises(TypeError, gender_field.validate_type, arguments['value'])

    @cases([
        {'value': 0},
        {'value': 1},
        {'value': 2},
    ])
    def test_GenderField_validate_content(self, arguments):
        gender_field = api.GenderField()
        gender_field.validate_content(arguments['value'])

    @cases([
        {'value': -1},
        {'value': 3},
    ])
    def test_GenderField_validate_content_error(self, arguments):
        gender_field = api.GenderField()
        self.assertRaises(api.ValidationError, gender_field.validate_content, arguments['value'])

    @cases([
        {'value': 1.0001},
        {'value': '0'},
        {'value': []},
        {'value': {}},
        {'value': ()},
    ])
    def test_GenderField_validate_content_TypeError(self, arguments):
        gender_field = api.GenderField()
        self.assertRaises(TypeError, gender_field.validate_content, arguments['value'])

    @cases([
        {'value': []},
        {'value': [0, 1, 2]},
    ])
    def test_ClientIDsField_validate_type(self, arguments):
        clientids_field = api.ClientIDsField()
        self.assertListEqual(clientids_field.validate_type(arguments['value']), arguments['value'])

    @cases([
        {'value': [0, 1, '2']},
        {'value': [0, 1, 2.0]},
    ])
    def test_ClientIDsField_validate_TypeError(self, arguments):
        clientids_field = api.ClientIDsField()
        self.assertRaises(TypeError, clientids_field.validate_type, arguments['value'])

    def test_ClientIDsField_validate_content(self):
        clientids_field = api.ClientIDsField()
        clientids_field.validate_content([0, 1, 2, 100000])

    def test_ClientIDsField_validate_content_error(self):
        clientids_field = api.ClientIDsField()
        self.assertRaises(api.ValidationError, clientids_field.validate_content, [-1, 0])


if __name__ == "__main__":
    unittest.main()
