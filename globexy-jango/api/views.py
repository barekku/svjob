from encodings.base64_codec import base64_decode
import json
import re
# import rsa
from urllib.error import HTTPError
from urllib.request import urlopen

from api.utils import prepare_command, rc_call, get_req_id, add_owner
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from jsonrpc import jsonrpc_method
from jsonrpc.exceptions import Error
from user import thread_local, redis_tokens_get
from user.utils import as_get_new_session_key, as_find_user


@jsonrpc_method('rc.find', safe=True)
def rc_find(request, *args, **kwargs):
    cmd = prepare_command('find', **kwargs)
    return rc_call(request, get_req_id(request), cmd)


@login_required
@jsonrpc_method('rc.insert', safe=True)
def rc_insert(request, *args, **kwargs):
    cmd = prepare_command('insert', **kwargs)
    add_owner(request, cmd, 'documents')
    return rc_call(request, get_req_id(request), cmd)


@login_required
@jsonrpc_method('rc.update', safe=True)
def rc_update(request, *args, **kwargs):
    cmd = prepare_command('update', **kwargs)
    add_owner(request, cmd, 'updates')
    return rc_call(request, get_req_id(request), cmd)


@login_required
@jsonrpc_method('rc.delete', safe=True)
def rc_delete(request, *args, **kwargs):
    cmd = prepare_command('delete', **kwargs)
    return rc_call(request, get_req_id(request), cmd)


@login_required
@jsonrpc_method('rc.getMore', safe=True)
def rc_getMore(request, *args, **kwargs):
    cmd = prepare_command('getMore', **kwargs)
    return rc_call(request, get_req_id(request), cmd)


@login_required
@jsonrpc_method('user.getNewSessionKey', safe=True)
def user_getNewSessionKey(request):
    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens is None:
        logout(request)
        err = Error('Authentication required.')
        err.code = 139
        err.status = 401
        raise err

    result, error = as_get_new_session_key(tokens)

    if result:
        # privkey = settings.SECRET_KEY.encode()
        # (pubkey, privkey) = rsa.newkeys(512)
        #result['key'] = rsa.encrypt(result['key'].encode(),pubkey)
        #result['pubkey'] = pubkey.n
        return result

    err = Error(error['message'])
    err.code = error['code']
    raise err


@login_required
@jsonrpc_method('user.findUser', safe=True)
def user_findUser(request, username=None, email=None):
    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens is None:
        logout(request)
        err = Error('Authentication required.')
        err.code = 139
        err.status = 401
        raise err

    result, error = as_find_user(tokens, username=username, email=email)

    if result:
        return result

    if error['code'] == 333:
        return "Not found"

    err = Error(error['message'])
    err.code = error['code']
    if settings.DEBUG:
        err.data = json.loads(request.body.decode('utf-8'))
    raise err


@login_required
@jsonrpc_method('document.convert(doc_oid=str, target_format=str)', safe=True)
def document_convert(request, doc_oid, target_format):
    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens is None:
        err = Error('Authentication required')
        err.code = 139
        err.status = 401
        raise err

    kwargs = {
        'cmdName_value': 'objects',
        'filter': {'_id': {'$oid': doc_oid}}
    }
    cmd = prepare_command('find', **kwargs)
    document = rc_call(request, get_req_id(request), cmd)

    if len(document['cursor']['firstBatch']) == 0:
        err = Error('Not found')
        err.status = 404
        raise err

    document = ['cursor']['firstBatch'][0]
    task = {
        'text': base64_decode(document['object']['text']),
        'convert_to': document['target_format'],
        'owner': request.user.as_user_id
    }
    try:
        resp = urlopen(settings.DOC_CONVERTER, task)
    except HTTPError as e:
        err = Error(e.msg)
        err.status = e.code
        err.data = e.read()
        raise err

    return json.loads(resp.read())


@login_required
@jsonrpc_method('document.get_converted(task=str)', safe=True)
def document_get_converted(request, task):
    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens is None:
        err = Error('Authentication required')
        err.code = 139
        err.status = 401
        raise err

    if not re.match(r'\d{10}-\d{18}', task):
        err = Error('Not found')
        err.status = 404
        raise err

    try:
        return urlopen('%s%s/%s' % (settings.DOC_CONVERTER, request.user.as_user_id, task))
    except HTTPError as e:
        err = Error(e.msg)
        err.status = e.code
        err.data = e.read()
        raise err
