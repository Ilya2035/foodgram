"""
Админка для приложения Users.

Этот модуль настраивает отображение моделей Profile и Subscription
в интерфейсе админки.
"""

from django.contrib import admin
from .models import Profile, Subscription


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Profile.

    Отображает данные профилей пользователей с возможностью поиска.
    """

    list_display = ('user', 'avatar')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Subscription.

    Показывает подписки пользователей и авторов, на которых они подписаны.
    """

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
