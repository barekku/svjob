from django.db import models
# from user.forms import EmailOrPhoneField
from user.validators import validate_phone_number
from django.utils.translation import ugettext_lazy as _


class PhoneNumberField(models.CharField):
    default_validators = [validate_phone_number]
    description = _("Phone number")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 20)
        super(PhoneNumberField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(PhoneNumberField, self).deconstruct()
        # We do not exclude max_length if it matches default as we want to change
        # the default in future.
        return name, path, args, kwargs

#     def formfield(self, **kwargs):
        # As with CharField, this will cause email validation to be performed
        # twice.
#         defaults = {
#             'form_class': EmailOrPhoneField,
#         }
#         defaults.update(kwargs)
#         return super(PhoneNumberField, self).formfield(**defaults)
