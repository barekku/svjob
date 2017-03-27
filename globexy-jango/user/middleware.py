from importlib import import_module

from django.conf import settings
from django.http.response import HttpResponseServerError
from django.utils.deprecation import MiddlewareMixin
from user import thread_local, redis_tokens_set, generate_tokens_key
from user.utils import as_login


class SaveSessionIdMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super(SaveSessionIdMiddleware, self).__init__(get_response)
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def process_request(self, request):
        if 'tokens_key' in request.session and request.session['tokens_key'] is not None:
            thread_local.tokens_key = request.session['tokens_key']

    def process_response(self, request, response):
        if hasattr(thread_local, 'tokens_key') and thread_local.tokens_key is not None:
            request.session['tokens_key'] = thread_local.tokens_key
            del(thread_local.tokens_key)

        return response


class AnonimousUserLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated():
            return

        if hasattr(thread_local, 'tokens_key') and thread_local.tokens_key is not None:
            return

        tokens, error = as_login(settings.ANONYMOUS_USER_NAME, settings.ANONYMOUS_USER_PASS)
        if error:
            return HttpResponseServerError()

        tokens_key = generate_tokens_key()
        redis_tokens_set(tokens_key, tokens)
        thread_local.tokens_key = tokens_key
