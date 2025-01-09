import django_filters

from recipes.models import Recipe
from ingredients.models import Ingredient


class RecipeFilter(django_filters.FilterSet):
    """
    Фильтры для модели Recipe.

    Поддерживает фильтрацию по тегам, автору, избранному и списку покупок.
    """

    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        """
        Метаданные для RecipeFilter.

        Указывает модель Recipe и поля для фильтрации.
        """

        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """
        Фильтрует рецепты по тегам.

        Использует параметр 'tags' из запроса для фильтрации рецептов.
        """
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрует рецепты, добавленные в избранное.

        Возвращает рецепты, которые пользователь отметил как избранные.
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрует рецепты, добавленные в список покупок.

        Возвращает рецепты, которые пользователь добавил в список покупок.
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    """
    Фильтр для модели Ingredient.

    Позволяет искать ингредиенты по началу названия (istartswith).
    """

    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')
