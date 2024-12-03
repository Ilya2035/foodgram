from django.db import models
from django.contrib.auth.models import User
from tags.models import Tag
from ingredients.models import Ingredient


class Recipe(models.Model):
    name = models.CharField(max_length=255)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    image = models.ImageField(upload_to='recipes/images/')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', related_name='recipes')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredient_links')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipe_links')
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        return f"{self.ingredient.name} для {self.recipe.name}"
