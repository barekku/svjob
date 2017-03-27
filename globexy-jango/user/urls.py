from django.conf.urls import url
from user.views import register, confirm, login, logout_page, status, change_password


urlpatterns = [
    url(r'^logout/?$', logout_page, name='logout'),
    url(r'^login/?$', login, name='login'),
    url(r'^register/?$', register, name='register'),
    url(r'^confirm/?$', confirm, name='confirm'),
    url(r'^status/?$', status, name='user_status'),
    url(r'^change-password/?$', change_password, name='change_password'),
]
