"""
Модели для приложения Users.

Этот модуль содержит модели Profile и Subscription для работы с профилями
пользователей и подписками.
"""

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Модель профиля пользователя.

    Атрибуты:
        user: Связанный пользователь.
        avatar: Аватар пользователя, загружается в директорию avatars/.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        """
        Возвращает строковое представление профиля.

        Возвращает имя пользователя.
        """
        return self.user.username


class Subscription(models.Model):
    """
    Модель подписки пользователя.

    Атрибуты:
        user: Пользователь, который подписан.
        author: Автор, на которого подписан пользователь.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers'
    )

    class Meta:
        """
        Метаданные для модели Subscription.

        Определяет уникальность пары (user, author).
        """

        unique_together = ['user', 'author']

    def __str__(self):
        """
        Возвращает строковое представление подписки.

        Формат: "user подписан на author".
        """
        return f"{self.user.username} подписан на {self.author.username}"
