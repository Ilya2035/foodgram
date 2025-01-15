from django.contrib import admin

from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Tag.

    Включает отображение, поиск и фильтрацию тегов.
    """

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
