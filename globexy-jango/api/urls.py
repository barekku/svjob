from django.conf import settings
from django.conf.urls import url
from jsonrpc.site import jsonrpc_site
import jsonrpc.views

import api.views  # Не удалять - нужно для регистрации методов


urlpatterns = []
if settings.DEBUG:
    # for the graphical browser/web console only, omissible
    urlpatterns.append(url(r'^browse/', jsonrpc.views.browse, name="jsonrpc_browser"))

urlpatterns.append(url(r'^$', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"))
