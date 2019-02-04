#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import unittest

import api


class TestFieldDescriptionSuite(unittest.TestCase):

    def setUp(self):
        pass

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


if __name__ == "__main__":
    unittest.main()
