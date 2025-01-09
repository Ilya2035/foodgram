from django.contrib import admin
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Recipe.
    Отображает основные данные о рецептах, фильтрацию, поиск.
    """
    list_display = ('name', 'author', 'cooking_time')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'cooking_time')
    filter_horizontal = ('tags', 'ingredients')
    inlines = [RecipeIngredientInline]

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для связи рецептов и ингредиентов."""
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для связей пользователя с рецептами в списках покупок."""
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранных рецептов пользователей."""
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
