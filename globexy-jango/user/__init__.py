import json
import random
import threading
import time

from django.conf import settings
import redis
import websocket


thread_local = threading.local()


def as_socket():
    if not hasattr(thread_local, 'auth_server_ws'):
        thread_local.auth_server_ws = websocket.create_connection(settings.AUTH_SERVER)

    return thread_local.auth_server_ws


def get_redis():
    if not hasattr(thread_local, 'redis_connection'):
        thread_local.redis_connection = redis.StrictRedis(
            settings.SESSION_REDIS_HOST,
            settings.SESSION_REDIS_PORT
        )

    return thread_local.redis_connection


def redis_tokens_set(key, tokens):
    get_redis().set(
        'tokens:%s' % key,
        json.dumps(tokens),
        ex=settings.SESSION_COOKIE_AGE
    )


def redis_tokens_get(key):
    tokens = get_redis().get('tokens:%s' % key)
    return json.loads(tokens.decode('UTF-8')) if tokens is not None else None


def redis_tokens_delete(key):
    get_redis().delete('tokens:%s' % key)


def generate_tokens_key():
    tokens_key = str(time.time()).split('.')
    tokens_key.reverse()
    tokens_key = ''.join(tokens_key).rjust(17, '0')[:17]
    tokens_key += str(random.random())[2:].rjust(15, '0')[-15:]
    return tokens_key
