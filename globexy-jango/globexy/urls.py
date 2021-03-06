"""globexy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
import django.views.static


# from django.views.generic.base import TemplateView
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    url(r'^user/', include('user.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^utils/', include('utils.urls')),
]

if settings.DEBUG:
    urlpatterns.append(
        url(
            r'^$',
            django.views.static.serve,
            kwargs={
                'path': 'index.html',
                'document_root': settings.POLYMER_GUI
            }
        )
    )
    urlpatterns.append(
        url(
            r'^(?P<path>.+)$',
            django.views.static.serve,
            kwargs={'document_root': settings.POLYMER_GUI}
        )
    )
