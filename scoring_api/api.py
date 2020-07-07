#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from datetime import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from .store import Store
from .scoring import get_score, get_interests


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
NoneType = type(None)


class ValidationError(Exception):
    pass


class Field(object):
    def __init__(self, required=False, nullable=True, *args, **kwargs):
        self.required = required
        self.nullable = nullable
        self.value = None
        self.name = None
        self.empty_values = ("", [], (), {})
        self.validators = []

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype):
        return obj.__dict__.get(self._name)

    def __set__(self, obj, value):
        self.check_validation(value)
        obj.__dict__[self._name] = value

    def validate(self, value):
        pass

    def check_validation(self, value):
        if (value is None and not self.required) or (
            self.nullable and value in self.empty_values
        ):
            return True
        if value is None and self.required:
            raise ValidationError("Value is required")
        if not self.nullable and value in self.empty_values:
            raise ValidationError("Value cannot be empty")
        self.validate(value)
        return True


class CharField(Field):
    empty_values = ("",)

    def validate(self, value):
        if not isinstance(value, (str)):
            raise ValidationError("Value must be a string")


class ArgumentsField(Field):
    empty_values = ({},)

    def validate(self, value):
        if not isinstance(value, (dict)):
            raise ValidationError("Value must be a dict")


class EmailField(CharField):
    empty_values = ("",)

    def validate(self, value):
        super().validate(value)
        if "@" not in value:
            raise ValidationError("Value must be a valid email address")


class PhoneField(Field):
    empty_values = ("",)

    def validate(self, value):
        if not isinstance(value, (str, int)) or not re.match(
            r"^7[0-9]{10}", str(value)
        ):
            raise ValidationError("Value must be a valid phone number")


class DateField(CharField):
    empty_values = ("",)

    def validate(self, value):
        super().validate(value)
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}", value):
            raise ValidationError("Value must be a valid date")


class BirthDayField(DateField):
    empty_values = ("",)

    def validate(self, value):
        super().validate(value)
        max_years_diff = 70
        date = datetime.strptime(value, "%d.%m.%Y")
        diff_years = (datetime.now() - date).days / 365.25
        if diff_years < 0 or diff_years >= max_years_diff:
            raise ValidationError(
                "Value can't be future or more than 70 years ago from now"
            )


class GenderField(Field):
    empty_values = ("",)

    def validate(self, value):
        if not isinstance(value, int):
            raise ValidationError("Value must be integer")
        if value not in (UNKNOWN, MALE, FEMALE):
            raise ValidationError("Value must be valid gender code")


class ClientIDsField(Field):
    empty_values = ([],)

    def validate(self, value):
        is_valid = (
            isinstance(value, list)
            and all(isinstance(i, int) for i in value)
        )
        if not is_valid:
            raise ValidationError("Value must be a list of integers")


class RequestMeta(type):
    def __call__(self, *args, **kwargs):
        self.fields = [
            f for f in self.__dict__ if isinstance(self.__dict__.get(f), Field)
        ]
        return super().__call__(*args, **kwargs)


class BaseRequest(metaclass=RequestMeta):
    fields = ()

    def __init__(self, *args, **kwargs):
        self.set_values(kwargs)

    def set_values(self, kwargs):
        errors = {}
        for field in self.fields:
            try:
                setattr(self, field, kwargs.get(field))
            except ValidationError as e:
                if not errors.get(field):
                    errors[field] = []
                errors[field].append(str(e))

        if errors:
            raise ValidationError(errors)


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate()

    def validate(self):
        def is_valid_pair(a, b):
            return a is not None and b is not None

        any_pair_valid = any(
            (
                is_valid_pair(self.phone, self.email),
                is_valid_pair(self.first_name, self.last_name),
                is_valid_pair(self.gender, self.birthday),
            )
        )
        if any_pair_valid:
            return

        raise ValidationError(
            ("Must contain at least one pair of values(phone/email , first_name/last_name , gender/birtday)")
        )


class MethodRequest(BaseRequest):
    account = CharField(required=True, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    login = request.login or ""
    account = request.account or ""
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512((account + login + SALT).encode("utf-8")).hexdigest()
    if digest == request.token:
        return True
    return False


def get_online_score(request, store):
    score = get_score(
        store,
        request.phone,
        request.email,
        request.birthday,
        request.gender,
        request.first_name,
        request.last_name,
    )
    return {"score": score}


def get_client_interests(request, store):
    result = {}
    if request.client_ids:
        for id in request.client_ids:
            result[id] = get_interests(store, None)
    return result


def online_score_handler(method, arguments, ctx, store):
    if method.is_admin:
        return {"score": 42}, OK
    online_score = OnlineScoreRequest(**arguments)
    ctx["has"] = [
        field for field in online_score.fields
        if getattr(online_score, field) is not None
    ]
    return get_online_score(online_score, store), OK


def clients_interests_handler(arguments, ctx, store):
    clients_interests = ClientsInterestsRequest(**arguments)
    ctx["nclients"] = (
        len(clients_interests.client_ids)
        if clients_interests.client_ids
        else 0
    )
    return get_client_interests(clients_interests, store), OK


def method_handler(request, ctx, store):
    request_body = request.get("body")

    try:
        method_request = MethodRequest(
            account=request_body.get("account"),
            login=request_body.get("login"),
            method=request_body.get("method"),
            token=request_body.get("token"),
            arguments=request_body.get("arguments"),
        )

        if not check_auth(method_request):
            return None, FORBIDDEN

        arguments = {}
        if method_request.arguments is not None:
            arguments = method_request.arguments

        if method_request.method == "online_score":
            return online_score_handler(method_request, arguments, ctx, store)
        if method_request.method == "clients_interests":
            return clients_interests_handler(arguments, ctx, store)
    except ValidationError as errors:
        return str(errors), INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = Store()

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store
                    )
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
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
