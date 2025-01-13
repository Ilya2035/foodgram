from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.db import models


class FoodgramUserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя."""

    def create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        password=None,
        **extra_fields
    ):
        """Создаёт и сохраняет пользователя с указанными данными."""
        if not email:
            raise ValueError('Пользователь должен иметь email.')
        if not username:
            raise ValueError('Пользователь должен иметь username.')
        if not first_name:
            raise ValueError('Пользователь должен иметь имя.')
        if not last_name:
            raise ValueError('Пользователь должен иметь фамилию.')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        username,
        first_name,
        last_name,
        password=None,
        **extra_fields
    ):
        """Создаёт и сохраняет суперпользователя с указанными данными."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(
            email,
            username,
            first_name,
            last_name,
            password,
            **extra_fields
        )


class FoodgramUser(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=255,
        unique=True
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=150,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=30
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        verbose_name='Активен',
        default=True
    )
    is_staff = models.BooleanField(
        verbose_name='Сотрудник',
        default=False
    )
    date_joined = models.DateTimeField(
        verbose_name='Дата регистрации',
        auto_now_add=True
    )

    objects = FoodgramUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Мета класс для модели FoodgramUser."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает строковое представление пользователя."""
        return self.email


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
        """Мета класс для модели Subscription."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f"{self.user} подписан на {self.author}"
