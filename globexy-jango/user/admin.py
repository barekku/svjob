from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.utils.translation import ugettext_lazy as _
from user.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(_UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password', 'as_user_id')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
