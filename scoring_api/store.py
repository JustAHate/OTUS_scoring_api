import redis
import logging


class StoreAccessException(Exception):
    pass


class Store:
    def __init__(self, host, port, timeout):
        self.messages = {
            'connection_error': 'Can\'t connect to redis'
        }
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
            logging.error(self.messages.get('connection_error'))
            raise StoreAccessException('Can\'t connect to store')
        return cached_value

    def cache_set(self, key, value, expire):
        try:
            self.store.set(key, value)
            self.store.expire(key, expire)
            return key, value, expire
        except redis.exceptions.ConnectionError:
            logging.info(self.messages.get('connection_error'))
            return None

    def cache_get(self, key):
        try:
            cached_value = self.store.get(key)
        except redis.exceptions.ConnectionError:
            logging.info(self.messages.get('connection_error'))
            return None
        return cached_value
