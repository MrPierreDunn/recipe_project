import re

from django.core.exceptions import ValidationError


def validate_username_uniqueness(value):
    if value == 'me':
        raise ValidationError(
            'Имя пользователя "me" не разрешено.'
        )
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Недопустимые символы :', re.sub(r'[\w.@+-]+', '', value)
        )
    return True
