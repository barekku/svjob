from django.conf.urls import url
from utils.views import get_qrcode


urlpatterns = [
    url(r'^qrcode/(?P<oid>[0-9A-Fa-f]{24})\.png$', get_qrcode, name='qrcode'),
]
