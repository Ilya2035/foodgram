from django.core.exceptions import ValidationError


def validate_username_not_me(value):
    if value.lower() == 'me':
        raise ValidationError('Использовать имя "me"'
                              ' в качестве username запрещено.')
    return value
