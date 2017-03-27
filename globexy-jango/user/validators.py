from django.core.validators import RegexValidator, _lazy_re_compile
from django.utils.translation import ugettext_lazy as _


validate_phone_number = RegexValidator(
    _lazy_re_compile(r'^\+\d{11,20}$'),
    message=_('Enter a valide phone number'),
    code='invalid',
)
