import re

from django.core.exceptions import ValidationError


def validate_username_uniqueness(value):
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Недопустимые символы :', re.sub(r'[\w.@+-]+', '', value)
        )
    return True
