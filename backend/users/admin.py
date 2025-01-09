from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodgramUser, Subscription


@admin.register(FoodgramUser)
class CustomUserAdmin(UserAdmin):
    """
    Настройка интерфейса админки для модели CustomUser.

    Отображает данные пользователя (включая email, аватар),
    с возможностью поиска и фильтрации.
    """

    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name', 'avatar'
    )
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ("Персональная информация", {
            'fields': ('first_name', 'last_name', 'avatar')
        }),
        ("Права доступа", {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions')
        }),
        ("Даты", {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'avatar'
            ),
        }),
    )
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Subscription.

    Показывает подписки пользователей и авторов, на которых они подписаны.
    """

    list_display = ('user', 'author')
    search_fields = ('user__email', 'user__username', 'author__email',
                     'author__username')
    list_filter = ('user', 'author')