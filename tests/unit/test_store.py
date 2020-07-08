import pytest
from redis import Redis
from redis.exceptions import ConnectionError
import time
import subprocess
from scoring_api.store import Store, StoreAccessException


@pytest.fixture()
def redis_fixture():
    port = '6380'
    redis_process = subprocess.Popen(['redis-server', '--port', port])
    time.sleep(0.1)
    _redis = Redis(port=port)
    yield
    redis_process.terminate()
    redis_process.wait()


def test_store_connection_ok(redis_fixture):
    store = Store('127.0.0.1', 6380, 5)
    assert store.store.ping()


def test_store_connection_bad():
    with pytest.raises(ConnectionError):
        store = Store('127.0.0.1', 6380, 5)
        assert store.store.ping()


def test_store_cache(redis_fixture):
    store = Store('127.0.0.1', 6380, 5)
    init_val = 'eggs'
    store.cache_set('spam', init_val, 60)
    assert store.cache_get('spam') == init_val


def test_store_storage_ok(redis_fixture):
    store = Store('127.0.0.1', 6380, 5)
    init_val = 'eggs'
    store.cache_set('spam', init_val, 60)
    assert store.get('spam') == init_val


def test_store_storage_bad():
    store = Store('127.0.0.1', 6380, 5)
    init_val = 'eggs'
    store.cache_set('spam', init_val, 60)
    with pytest.raises(StoreAccessException):
        assert store.get('spam') == init_val
