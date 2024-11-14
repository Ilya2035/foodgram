from django.conf import settings
from django.db import models
from recipes.models import Recipe


class ShoppingList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_list',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list_item'
            )
        ]
        ordering = ('-id',)

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в список покупок'
