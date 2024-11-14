from django.contrib import admin
from .models import ShoppingList


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    ordering = ('id',)
