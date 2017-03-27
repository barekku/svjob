import threading

from django.conf import settings
import websocket


def rc_socket():
    local_data = threading.local()
    if not hasattr(local_data, 'rc_server_ws'):
        local_data.rc_server_ws = websocket.create_connection(settings.RC_SERVER)

    return local_data.rc_server_ws
