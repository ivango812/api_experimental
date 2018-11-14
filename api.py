#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:
    """
    Base field class - serving common field settings and handling validation and data clean top-level logic
    """
    empty_values = (None, {}, [], (), "")

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if self.required and value is None:
            raise ValueError('Отсутствует обязательное поле')
        if not self.nullable and value in self.empty_values:
            raise ValueError('Поле не должно быть пустым')

    def validate_type(self, value):
        return value

    def validate_content(self, value):
        pass

    def clean(self, value):
        self.validate(value)
        value = self.validate_type(value)
        if value in self.empty_values:
            return value
        self.validate_content(value)
        return value


class CharField(BaseField):

    def validate_type(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("Поле должно быть строкой")
        return value


class ArgumentsField(BaseField):

    def validate_type(self, value):
        if value is not None and not isinstance(value, dict):
            raise TypeError("Не переданы аргументы")
        return value


class EmailField(CharField):

    def validate_type(self, value):
        value = super().validate_type(value)
        return value

    def validate_content(self, value):
        if '@' not in value:
            raise ValueError("Строка не является email-ом")


class PhoneField(BaseField):

    def validate_type(self, value):
        if value is None:
            return value
        if not isinstance(value, (str, int)):
            raise TypeError("Это поле должно быть задано числом или строкой")
        value = str(value)
        return value

    def validate_content(self, value):
        try:
            int(value)
        except ValueError:
            raise ValueError("Поле должно содержать только цифры 0-9")

        if len(value) != 11 or not value.startswith("7"):
            raise ValueError("Неверно указан номер телефона")


class DateField(CharField):

    def validate_type(self, value):
        value = super().validate_type(value)
        if value in self.empty_values:
            return value
        try:
            setattr(self, '_date', datetime.datetime.strptime(value, '%d.%m.%Y').date())
        except ValueError:
            raise ValueError('Не соответствует дате в формете DD.MM.YYYY')
        return value


class BirthDayField(DateField):

    def validate_content(self, value):
        today = datetime.date.today()
        age = today - getattr(self, '_date')
        if age.days / 365.25 > 70:
            raise ValueError('Возраст не должен быть > 70 лет')


class GenderField(BaseField):

    def validate_type(self, value):
        if value is not None and not isinstance(value, int):
            raise TypeError("Пол должен быть представлен числом 0, 1, 2")
        return value

    def validate_content(self, value):
        if value not in GENDERS:
            raise ValueError("Пол должен быть представлен числом 0, 1, 2")


class ClientIDsField(BaseField):

    def validate_type(self, value):
        if value is not None:
            if not isinstance(value, list) or not all(isinstance(v, int) for v in value):
                raise TypeError("Должен быть список целых чисел")
        return value

    def validate_content(self, value):
        if not all(v >= 0 for v in value):
            raise ValueError("Числа должны быть положительными")


class RequestMeta(type):
    """
    Meta class helps handle Request fields while Request class creates
    """

    def __new__(metaclass, class_name, class_parents, class_attr):
        # filter only BaseField objects
        api_fields = {
                    filed_name: field
                    for filed_name, field in class_attr.items()
                    if isinstance(field, BaseField)
                  }
        class_attr_cleaned = {
                    filed_name: field
                    for filed_name, field in class_attr.items()
                    if not isinstance(field, BaseField)
                  }
        class_attr_cleaned["_fields_raw_data"] = api_fields

        return super().__new__(metaclass, class_name, class_parents, class_attr_cleaned)


class Request(metaclass=RequestMeta):
    """
    Top-level logic on Request handling - such as validation, errors
    """
    def __init__(self, request):
        self.request = request
        self._errors = None
        self.non_empty_fields = []

    @property
    def errors(self):
        if self._errors is None:
            self.validate()
        return self._errors

    def is_valid(self):
        return not self.errors

    def validate(self):
        self._errors = {}
        fields = getattr(self, '_fields_raw_data').items()
        for name, field in fields:
            try:
                value = self.request.get(name)
                value = field.clean(value)
                setattr(self, name, value)
                if value not in field.empty_values:
                    self.non_empty_fields.append(name)
            except (TypeError, ValueError) as e:
                self._errors[name] = str(e)


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super().validate()
        if not self._errors:
            if self.phone and self.email:
                return
            if self.first_name and self.last_name:
                return
            if self.birthday and self.gender is not None:
                return
            self._errors["arguments"] = "Неверный список аргументов"


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class OnlineScoreHandler:

    @staticmethod
    def process_request(request, context, store):
        req = OnlineScoreRequest(request.arguments)
        if not req.is_valid():
            return req.errors, INVALID_REQUEST
        if request.is_admin:
            score = 42
        else:
            score = get_score(store, req.phone, req.email, req.birthday, req.gender, req.first_name, req.last_name)
        context["has"] = req.non_empty_fields
        return {"score": score}, OK


class ClientsInterestsHandler:

    @staticmethod
    def process_request(request, context, store):
        req = ClientsInterestsRequest(request.arguments)
        if not req.is_valid():
            return req.errors, INVALID_REQUEST
        context["nclients"] = len(req.client_ids)
        response_body = {cid: get_interests(store, cid) for cid in req.client_ids}
        return response_body, OK


def check_auth(request):
    if request.is_admin:
        string = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
    else:
        string = request.account + request.login + SALT
    digest = hashlib.sha512(str(string).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    handlers = {
        "online_score": OnlineScoreHandler,
        "clients_interests": ClientsInterestsHandler
    }

    method_request = MethodRequest(request["body"])
    if not method_request.is_valid():
        return method_request.errors, INVALID_REQUEST
    if not check_auth(method_request):
        return "Forbidden", FORBIDDEN

    handler = handlers[method_request.method]()
    return handler.process_request(method_request, ctx, store)


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(bytes(data_string).decode())
        except Exception as e:
            # print('Exception=', e)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
