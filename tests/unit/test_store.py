import pytest
from unittest.mock import MagicMock
import redis
from scoring_api.store import Store


class RedisMock:
    def get(self, *args):
        return 42

    def set(self, value, *args):
        pass

    def expire(self, *args):
        pass


@pytest.fixture()
def mock_redis_ok():
    redis.StrictRedis = MagicMock(return_value=RedisMock())


@pytest.fixture()
def mock_redis_bad(mock_redis_ok):
    redis.StrictRedis = MagicMock(side_effect=redis.exceptions.ConnectionError)


def test_store_connection_ok():
    store = Store()
    assert isinstance(store.store, redis.Redis)


def test_store_connection_bad(mock_redis_bad):
    with pytest.raises(redis.exceptions.ConnectionError):
        store = Store()
        assert isinstance(store.store, redis.Redis)


def test_store_get(mock_redis_ok):
    store = Store()
    assert store.get('spam') == 42


def test_store_set(mock_redis_ok):
    store = Store()
    assert store.set('spam', 'eggs', 180) == ('spam', 'eggs', 180)
