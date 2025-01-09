from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import (
    EmailValidator, RegexValidator, MaxLengthValidator
)
from django.utils.translation import gettext_lazy as _

from .constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
)

class FoodgramUser(AbstractUser):
    """
    Кастомная модель пользователя.

    - email используется в качестве USERNAME_FIELD (логин).
    - username, first_name и last_name в REQUIRED_FIELDS
      (требуется при создании суперпользователя).
    - avatar хранит аватар пользователя.
    """

    email = models.EmailField(
        _('email address'),
        max_length=USER_EMAIL_MAX_LENGTH,  # из констант
        unique=True,
        validators=[EmailValidator()],
        help_text="Используется как логин для входа в систему"
    )
    username = models.CharField(
        _('username'),
        max_length=USER_NAME_MAX_LENGTH,
        unique=True,
        help_text=_(
            "Обязательное. 150 символов или меньше. "
            "Только буквы, цифры и @/./+/-/_."
        ),
        validators=[
            RegexValidator(
                r'^[\w.@+-]+\Z',
                _("Введите корректный юзернейм.")
            ),
            MaxLengthValidator(USER_NAME_MAX_LENGTH)
        ],
        error_messages={
            'unique': _("Пользователь с таким именем уже существует."),
        },
    )
    first_name = models.CharField(
        _('first name'),
        max_length=USER_FIRST_NAME_MAX_LENGTH,
        blank=True
    )
    last_name = models.CharField(
        _('last name'),
        max_length=USER_LAST_NAME_MAX_LENGTH,
        blank=True
    )

    avatar = models.ImageField(
        _("Аватар"),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Загрузите изображение в одном из поддерживаемых форматов"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.email})"


class Subscription(models.Model):
    """
    Модель подписки пользователя.

    user   — подписчик (тот, кто подписывается).
    author — автор, на которого подписываются.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
