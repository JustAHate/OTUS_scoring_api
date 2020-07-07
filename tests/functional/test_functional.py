import pytest
import hashlib
from scoring_api import api
import datetime


def get_response(data, ctx, headers, store):
    return api.method_handler({"body": data, "headers": headers}, ctx, store)


class MockStore():
    def get(self, *args):
        return None

    def cache_get(self, *args):
        return None

    def cache_set(self, *args):
        pass


@pytest.fixture
def get_request_data():
    ctx = {}
    headers = {}
    store = MockStore()
    return ctx, headers, store


@pytest.fixture
def get_request_with_auth():
    def _get_request_with_auth(body=None):
        if body is None:
            body = {"account": "horns&hoofs", "login": "h&f", "method": "online_score"}
        if body.get("login") == api.ADMIN_LOGIN:
            body["token"] = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            msg = body.get("account", "") + body.get("login", "") + api.SALT
            body["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()
        return body
    return _get_request_with_auth


@pytest.fixture
def get_valid_auth_request():
    return {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'token': '55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95'}


def test_empty_request(get_request_with_auth, get_request_data):
    data = get_request_with_auth()
    ctx, headers, store = get_request_data
    response, code = get_response(data, ctx, headers, store)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize(
    'body', (
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    )
)
def test_bad_auth(body, get_request_data):
    ctx, headers, store = get_request_data
    response, code = get_response(body, ctx, headers, store)
    assert code == api.FORBIDDEN


@pytest.mark.parametrize(
    'body', (
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    )
)
def test_invalid_method_request(body, get_request_with_auth, get_request_data):
    data = get_request_with_auth(body)
    ctx, headers, store = get_request_data
    response, code = get_response(data, ctx, headers, store)
    assert code == api.INVALID_REQUEST
    assert bool(len(response))


@pytest.mark.parametrize(
    'arguments', (
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
    )
)
def test_invalid_score_request(arguments, get_valid_auth_request, get_request_data):
    request = get_valid_auth_request
    request['arguments'] = arguments
    ctx, headers, store = get_request_data
    response, code = get_response(request, ctx, headers, store)
    assert code == api.INVALID_REQUEST
    assert bool(len(response))


@pytest.mark.parametrize(
    'arguments', (
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    )
)
def test_ok_score_request(arguments, get_valid_auth_request, get_request_data):
    request = get_valid_auth_request
    request['arguments'] = arguments
    ctx, headers, store = get_request_data
    response, code = get_response(request, ctx, headers, store)
    assert code == api.OK
    score = response.get("score")
    assert isinstance(score, (int, float)) and score >= 0, arguments
    assert sorted(ctx["has"]) == sorted(arguments.keys())


def test_ok_score_admin_request(get_request_with_auth, get_request_data):
    arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
    body = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
    req = get_request_with_auth(body)
    req['arguments'] = arguments
    ctx, headers, store = get_request_data
    response, code = get_response(req, ctx, headers, store)
    assert code == api.OK
    score = response.get("score")
    assert score == 42


@pytest.mark.parametrize(
    'arguments', (
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    )
)
def test_invalid_interests_request(arguments, get_valid_auth_request, get_request_data):
    request = get_valid_auth_request
    request['arguments'] = arguments
    ctx, headers, store = get_request_data
    response, code = get_response(request, ctx, headers, store)
    assert code == api.INVALID_REQUEST
    assert bool(len(response))


@pytest.mark.parametrize(
    'arguments', (
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    )
)
def test_ok_interests_request(arguments, get_request_with_auth, get_request_data):
    body = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests"}
    request = get_request_with_auth(body)
    request['arguments'] = arguments
    ctx, headers, store = get_request_data
    response, code = get_response(request, ctx, headers, store)
    assert code == api.OK
    assert len(arguments["client_ids"]) == len(response)
    assert ctx.get("nclients") == len(arguments["client_ids"])

