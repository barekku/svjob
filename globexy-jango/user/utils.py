import hashlib
import json
from random import random
import time

from django.conf import settings
from jsonrpc.exceptions import Error
import redis_lock
from user import as_socket, get_redis, thread_local, redis_tokens_get, redis_tokens_set, \
    redis_tokens_delete, generate_tokens_key


def send_command(command, tokens, params=None):
    ws = as_socket()

    req = {
        "jsonrpc": "2.0",
        "method": command,
        "params": params or {},
        "id": "aidishnik"
    }

    while True:
        req['params']["token_short"] = tokens['token_short']
        req['params']["token_long"] = tokens['token_long']
        r = json.dumps(req)
        if settings.DEBUG:
            print('AuthServer: Request: ================================================')
            print(r)
            print('AuthServer: Request: ------------------------------------------------')

        ws.send(r)
        response = ws.recv()
        if settings.DEBUG:
            print('AuthServer: Response: ================================================')
            print(response)
            print('AuthServer: Response: ------------------------------------------------')
        response = json.loads(response)

        if 'result' in response:
            return response['result'], None

        if response['error']['code'] == 139 or response['error']['code'] == -32011:
            tokens, error = as_token_reniew(thread_local.tokens_key, tokens)
            if error:
                return None, response['error']

            continue

        if 'error' in response:
            return None, response['error']


def as_token_reniew(tokens_key, current_tokens):
    print('*** as_token_reniew() ***')
    ws = as_socket()
    lock = None

    while True:
        tokens = redis_tokens_get(tokens_key)
        if time.time() - tokens['ts'] < 55 and tokens['token_short'] != current_tokens['token_short']:
            return tokens, None

        if lock is None:
            lock = redis_lock.Lock(get_redis(), tokens_key, expire=10)

        locked = False
        try:
            locked = lock.acquire(blocking=False)
            if not locked:
                time.sleep(0.1)
                continue

            # http://gitlab.0070.ru/DataEcosystem/AuthServer/wikis/TokenRenew_command
            req = {
                "method": "TokenRenew",
                "params": {
                    "token_short": tokens['token_short'],
                    "token_long": tokens['token_long']
                },
                "id": "aidishnik"
            }

            ws.send(json.dumps(req))
            response = ws.recv()
            response = json.loads(response)

            if 'error' in response:
                return None, response['error']

            tokens['token_short'] = response['result']['token_short']
            tokens['ts'] = time.time()
            redis_tokens_set(tokens_key, tokens)
            return tokens, None
        except redis_lock.AlreadyAcquired:
            print('*> as_token_reniew() > redis_lock.AlreadyAcquired')
            time.sleep(random.random())
            continue
        finally:
            if locked:
                lock.release()

def as_confirm(request):
    ws = as_socket()

    # http://gitlab.0070.ru/DataEcosystem/AuthServer/wikis/Registrate_command
    m = request.POST.get('email')
    k = request.POST.get('regkey')
    req = {
        "method": "Register",
        "params": {
            "email": m,
            "reg_key": k
        },
        "id": "aydishnik"
    }
    ws.send(json.dumps(req))
    response = ws.recv()
    response = json.loads(response)
    
    print(response)

    if 'error' in response:
        return None, response['error']
    return response['result'], None

def as_register(request, username, email, password):
    ws = as_socket()

    # http://gitlab.0070.ru/DataEcosystem/AuthServer/wikis/Registrate_command
    req = {
        "method": "Register",
        "params": {
            "login": username,
            "email": email,
            "password": password
        },
        "id": "aydishnik"
    }
    ws.send(json.dumps(req))
    response = ws.recv()
    response = json.loads(response)

    if 'error' in response:
        return None, response['error']

    # tokens, error = as_login(username, password)
    # if error:
    #     return None, error

    # result, error = as_authenticate(tokens)
    # if error:
    #     return None, error

    anon_tokens = redis_tokens_get(thread_local.tokens_key)
    # if anon_tokens:
    #     as_logout(anon_tokens)
    # redis_tokens_delete(thread_local.tokens_key)

    # tokens_key = generate_tokens_key()
    # redis_tokens_set(tokens_key, tokens)
    # thread_local.tokens_key = tokens_key

    # try:
    #     from api.utils import prepare_command, rc_call

    #     params = {
    #         "cmdName_value": "profiles",
    #         "documents": [
    #             {
    #                 "meta": {
    #                     "type": "public",
    #                     "owner": {"$oid": result["user_id"]},
    #                     "pattern": {"$oid": "582a963b717ce748cc017a58"},
    #                     "r": ["All"]
    #                 },
    #                 "profile": {
    #                     "name": "",
    #                     "surname": "",
    #                     "patronymic": "",
    #                     "avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAMAAACahl6sAAAB3VBMVEXf5ene5OjP1tvFz"
    #                     "dO3wMertbylsLidqbGXpKyUoaqVoqqXo6ycqLCirraptLu0vsTCytDM1Nnc4ua5wsmnsrqYpK2PnKWWoqujrra2v8bK0tfN1Nqyv"
    #                     "MOtuL/I0Nba4OS9xsygq7Obp6+4wcjV3OHW3OGRnqeuuL/Q2Ny2wMast77U2+C/yM7R2N3Hz9S7xMqxu8Lb4uaps7ueqrLS2d6apq"
    #                     "/I0NWQnaa8xcvAyc+0vcSwusGzvcPHz9XQ19zZ4OSVoarN1dqgrLSkr7fO1tuYpa3X3eKjr7bX3uKZpa6nsbnT2t/EzNKvucCSnqeXo"
    #                     "6u+x82irbXc4+eSn6jL09jH0NW6w8nGztPGztSyu8K3wce6w8rFztPb4eWUoamYpKy0vsXDzNGapq7V3OCuucDEzdKSn6fO1dq1v8WW"
    #                     "o6vZ3+SRnaafq7PY3uPL0tihrbTc4ueToKjCy9DJ0dbCy9GTn6jY3+PByc+str7d5OjAyM7DzNK8xsytt76os7qqtbylsLemsbizvcS"
    #                     "rtb2msbmqtLystr3d4+ensrm4wsjW3eLa4eW7xMuToKnW3eGcp7CUoKnBytC1v8aZpa3b4ea6xMqhrLS5wsifqrK5w8m1vsXJ0dfU29/"
    #                     "P19yeqbLC/n6VAAAE2UlEQVR4Ae3YiVJUVxcF4HUBaRUERVzdoDIFG2QSlNgMEZrQIAmigCSiDGEwoIGoiUMGRcXfiDHRGDXz8Kx/VVI"
    #                     "pExW59/YZNtT53mDVrnP2rgXHcRzHcRzHcRzHcZx1ysvIzNqUHdm8ZevWrVtycrfl5W/fUYD1JmNn4S6+LBorKl5HYXbvyeXqNu8twXpQ"
    #                     "WlbOtVS8UQnh9uVH6Ue8qhqCle6P07eaWkhVF2UQ8SIPEtXHGFRFA+Q5wDAaIUzTQYZzqBmSVL/JsOKZkONwgmlogRStTE+b0BzBtUOCO"
    #                     "qbvLdh3hCrsh20dVKMVdnUmqUgXrHqbqiSbYFER1emGPSmqVAZreqhULyzJolpHYUcfVSuBFXlU7R3YUE/1tsOCd6leD8zrpw7HYNwAdY"
    #                     "jAtILj1CIFw1qpRxUMi1GPpAej+qjLYRhVR10G5G91idvdO0FtmmFQNfUZFPj5yn8kjdRnCAZ1U5/oMMypoEb9MKbzJDUaEXfCyz/lu6h"
    #                     "TC4x5jzq9D2NOUaciGDNKnU67IIFlUqczMKaEOo2Ja+Hlt/K11GkcxkxMUqMumJNLfRKVNnpfDT7wYM4U9emGQdPUZw8M6qc+0zBphtrMw"
    #                     "qSz1CUCoz6kLm0wamKOmszDrINWql8NGqjHOZh2nlrUwrQs6tAN4z5aoAY7YF471VuEBR9TvQuwoY2qXYQVlz6hYvWw41OqNQBbhqhSchi2"
    #                     "9CWo0GXYc4XqNMKmvVQlArsWqcbVa7Cr8zyVmIdt/XEqkAn7di8wbZ9Bgq4E0zQIGeaTTMsVSFGZy/DilyFHQSHDym2GKGcYzudfQJiRCgY"
    #                     "39yXkGd7DoPIqIVIqm0HkjkKs64v0a+aGB8nGY/SjosWDdCNLk3y9hZuZWBdKt9+KcjXHb5fNYv2YKC5a7uGLci7mj/dh3fHqG1ru/O/uUC"
    #                     "wWG8r+qnHs1PwlOFqVjkClJtjR35bkvRUoM5VcSsG8jJoESUZSUKNvmSTvF8Os2hr+42uocH0L/3Z0B8zxziX43FAK6erdxOdqHsCQyxX8r"
    #                     "7ZvkJZvJ/lvD8tggtfOl+TUIbzRcr7o9iNo1xHhq3x3HeGMZPMVHh+DZt9zNYutwwhsPJurmIJWT/gaT/f3I4jOwUNcXeEK9LnFNRROl8Ifr"
    #                     "2TvY75W5AE0WTnKtUXvTfdhLRNHTs9wTTm10MIrpz8L3edKVg/z7MIPN5P05XEGNFj5kQFcjdT8dCxjXxOeW+ltbjjQXh6lf3PVUK+cIZyID"
    #                     "N0t/Evs554EA5uchWrLtCKnE2oN0JKIB5V+oTXLUKiEFv0KZR4laNM4VInQqkQv1DhNyyJQ4jdaNwUFViZpXwrpq6EAT5G2EYqQj3Ttogy/I"
    #                     "z07KcQQ0nKNYmQiHZsoxgmkoZ6CjCG8bgoSL0BYHRQly8pANDhZgHD+IDfGSO5SmLlhhFFLcW4gjHaKswshPJujPA0IbpACxRBcLiWatbIM"
    #                     "NXiCoBopUg4C8qKUqRjBHKFQSwhmiUIlPQThJSlVCYK4QLEGEMQditWDICKUqwP+zVKwMfjXSsHuw78BCpZcgW9/UrIU/Lq2QMnK4FcxRa"
    #                     "uCXy0UrRx+VVG0hwXwaRtlq4dPM5RtFD7FKVsZfKJwRRslyNmNEiRvowTpxobnOI7jOI7jOI7jOP8HnuF7Pck31hUAAAAASUVORK5CYII="
    #                 }
    #             }
    #         ]
    #     }
    #     cmd = prepare_command('insert', **params)
    #     req_id = '%s-%i' % (result['user_id'], time.time())
    #     rc_call(request, req_id, cmd)

    #     params = {
    #         "cmdName_value": "objects",
    #         "documents": [
    #             {
    #                 "meta": {
    #                     "owner": {"$oid": result['user_id']},
    #                     "description": "Shared prototypes and objects to current user",
    #                     "name": "<some calculated name>",
    #                     "pattern": {
    #                          "$oid": "58414646a4ba7bce4fa6042b"
    #                     }
    #                 },
    #                 "schema": {
    #                     "properties": {
    #                         "prototypes": {
    #                             "properties": [],
    #                             "type": "array"
    #                         },
    #                         "objects": {
    #                             "properties": [],
    #                             "type": "array"
    #                         }
    #                     },
    #                     "type": "object",
    #                     "required": [
    #                         "prototypes",
    #                         "objects"
    #                     ]
    #                 },
    #                 "SA_wishes": {
    #                     "wikiRefer": "https://en.wikipedia.org/wiki/Shared_resource"
    #                 },
    #             }
    #         ]
    #     }
    #     cmd = prepare_command('insert', **params)
    #     req_id = '%s-%i' % (result['user_id'], time.time())
    #     rc_call(request, req_id, cmd)
    # except Error as e:
    #     return None, {'code': e.code, 'messsage': e.message}

    # as_logout(tokens)

    return response['result'], None


def as_login(username, password):
    ws = as_socket()

    # http://gitlab.0070.ru/DataEcosystem/AuthServer/wikis/Login_command
    req = {
        "method": "Login",
        "params": {
            "login": username,
            "password": password
        },
        "id": "aidishnik"
    }

    ws.send(json.dumps(req))
    response = ws.recv()
    response = json.loads(response)

    if 'error' in response:
        return None, response['error']

    response['result']['ts'] = time.time()
    return response['result'], None


def as_logout(tokens):
        return send_command("Logout", tokens)


def as_authenticate(tokens):
    return send_command("Authenticate", tokens)


def as_user_profile(tokens):
    return send_command("UserProfile", tokens)


def as_get_new_session_key(tokens):
    signature = tokens['token_short'] + tokens['token_long'] + settings.SERVER_ID + settings.SECRET_KEY
    return send_command(
        "NewSessionRequest",
        tokens,
        {
            "server_id": settings.SERVER_ID,
            "signature": hashlib.sha256(bytes(signature, 'UTF-8')).hexdigest()
        }
    )


def as_change_password(tokens, old_pass, new_pass):
    if not old_pass:
        return None, {'code': 139, 'message': "Old password cannot be empty"}

    if not new_pass:
        return None, {'code': 139, 'message': "New password cannot be empty"}

    return send_command("ChangePassword", tokens, {"old_pass": old_pass, "new_pass": new_pass})


def as_find_user(tokens, username=None, email=None):
    if not username and not email:
        return None, {"code": 333, "message": "Item not found."}

    params = {
        "login": username,
        "email": email
    }
    return send_command("FindUserBy", tokens, params)
