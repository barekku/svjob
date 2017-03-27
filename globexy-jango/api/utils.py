from collections import OrderedDict
import json
from xmlrpc.client import Error

from api import rc_socket
from django.conf import settings
from django.contrib.auth import logout
from jsonrpc.exceptions import InvalidParamsError
from user import redis_tokens_get, thread_local
from user.utils import as_token_reniew


COMMAND_PARAMS = {
    'find': ("filter", "sort", "projection", "hint", "skip", "limit",
             "batchSize", "singleBatch", "comment", "maxScan", "maxTimeMS",
             "readConcern", "max", "min", "returnKey", "showRecordId",
             "snapshot", "tailable", "oplogReplay", "noCursorTimeout",
             "awaitData", "allowPartialResults"),
    "insert": ("documents", "ordered", "writeConcern", "bypassDocumentValidation"),
    "update": ("updates", "ordered", "writeConcern", "bypassDocumentValidation"),
    "delete": ("deletes", "ordered", "ordered", "writeConcern"),
    "getMore": ("collection", "batchSize", "maxTimeMS"),
}


def rc_call(request, req_id, cmd):
    ws = rc_socket()

    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens is None:
        logout(request)
        err = Error('Authentication required.')
        err.code = 139
        err.status = 401
        if settings.DEBUG:
            err.data = cmd
        raise err

    while True:
        # http://gitlab.0070.ru/DataEcosystem/Request_Controller/wikis/Protocol
        req = {
            "v": "1.0",
            "id": str(req_id),
            "tokens": {
                "token_long": tokens['token_long'],
                "token_short": tokens['token_short'],
            },
            'cmd': cmd
        }
        if settings.DEBUG:
            print('===###===')
            print(json.dumps(req))
            print(req)
            print('---***---')
        ws.send(json.dumps(req))
        response = ws.recv()
        response = json.loads(response)

        # TODO: Удалить, как закончим с отладкой
        if settings.DEBUG:
            print('===###===')
            #print(response)
            print('---***---')

        if 'result' in response:
            return response['result']

        if response['error']['code'] == 139 or response['error']['code'] == -32011:
            tokens, error = as_token_reniew(thread_local.tokens_key, tokens)
            if error:
                # Token reniewing failed. Logout and raise exception.
                logout(request)
                err = Error(error['message'])
                err.code = 139
                err.status = 401
                if settings.DEBUG:
                    err.data = cmd
                raise err

            continue

        err = Error(response['error']['message'])
        err.code = response['error']['code']
        if settings.DEBUG:
            err.data = cmd
            print('!!! === ERROR === !!!')
            print(response['error'])
            print('!!! === ERROR === !!!')

        raise err


def prepare_command(cmd_name, **kwargs):
    if settings.DEBUG:
        # TODO: Удалить, как закончим с отладкой
        print('===###===')
        print(kwargs)
        print('---***---')

    cmd = OrderedDict()
    cmd[cmd_name] = kwargs['cmdName_value']
    for p in COMMAND_PARAMS[cmd_name]:
        if p in kwargs:
            cmd[p] = kwargs[p]

    return cmd


def get_req_id(request):
    if request.method.lower() == 'get':
        return 'jsonrpc'

    if hasattr(request, "body"):
        D = json.loads(request.body.decode('utf-8'))
    else:
        D = json.loads(request.raw_post_data.decode('utf-8'))

    return D['id']


def add_owner(request, cmd, data_list_name):
    if data_list_name not in cmd or cmd[data_list_name] is None or len(cmd[data_list_name]) == 0:
        error = InvalidParamsError()
        if settings.DEBUG:
            error.data = cmd
        raise error

    for d in cmd[data_list_name]:
        if 'meta' not in d:
            d['meta'] = dict()
        d['meta']['owner'] = {'$oid': request.user.as_user_id}
