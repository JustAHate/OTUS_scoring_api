import redis
import logging

CONFIG = {
    'REDIS_HOST': 'localhost',
    'REDIS_PORT': '6379',
    'REDIS_TIMEOUT': 5
}


class Store:
    def __init__(self):
        self.messages = {
            'connection_error': 'Can\'t connect to redis'
        }
        host = CONFIG.get('REDIS_HOST')
        port = CONFIG.get('REDIS_PORT')
        timeout = CONFIG.get('REDIS_TIMEOUT')
        self.store = redis.StrictRedis(
            host=host,
            port=port,
            socket_timeout=timeout,
            decode_responses=True,
            retry_on_timeout=True
        )

    def get(self, key):
        try:
            cached_value = self.store.get(key)
        except redis.exceptions.ConnectionError:
            logging.info(self.messages.get('connection_error'))
            return None
        return cached_value

    def set(self, key, value, expire):
        try:
            self.store.set(key, value)
            self.store.expire(key, expire)
            return key, value, expire
        except redis.exceptions.ConnectionError:
            logging.info(self.messages.get('connection_error'))
            return None

    def cache_get(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def cache_set(self, *args, **kwargs):
        return self.set(*args, **kwargs)
