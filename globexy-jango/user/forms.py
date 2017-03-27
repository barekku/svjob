from __future__ import unicode_literals

from django import forms
from django.core import validators, exceptions
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy as _
from user.models import User
from user.validators import validate_phone_number


class EmailOrPhoneField(forms.CharField):
    widget = TextInput
    default_validators = [validators.validate_email, validate_phone_number]

    def __init__(self, *args, **kwargs):
        super(EmailOrPhoneField, self).__init__(*args, **kwargs)
        self.success_validations = []

    def clean(self, value):
        value = self.to_python(value).strip()
        return super(EmailOrPhoneField, self).clean(value)

    def run_validators(self, value):
        if value in self.empty_values:
            return

        errors = []
        for v in self.validators:
            try:
                v(value)
                self.success_validations.append(v)
            except exceptions.ValidationError as e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    e.message = self.error_messages[e.code]
                errors.extend(e.error_list)

        if len(errors) == len(self.validators):
            raise exceptions.ValidationError(errors)


class RegistrationForm(forms.Form):

    username = forms.RegexField(
        regex=r'^[\w.-]+$',
        widget=forms.TextInput(attrs=dict(required=True, max_length=150)),
        label=_("Username"),
        error_messages={'invalid': _("This value must contain only letters, numbers and underscores.")},
        max_length=150
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs=dict(required=True, max_length=254)),
        label=_("Email address")
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs=dict(
            required=True,
            max_length=128,
            render_value=False
        )),
        label=_("Password"),
        min_length=6,
        max_length=128,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs=dict(
            required=True,
            max_length=128,
            render_value=False
        )),
        label=_("Password (again)"),
        min_length=6,
        max_length=128,
    )

    def clean_username(self):
        try:
            User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']

        raise forms.ValidationError(_("The username already exists. Please try another one."))

    def clean(self):
        if 'password' in self.cleaned_data and 'password_confirm' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
                raise forms.ValidationError(_("The two password fields did not match."))

        return self.cleaned_data
