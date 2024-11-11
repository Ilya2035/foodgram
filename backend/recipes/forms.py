from django import forms
from .models import Recipe


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ('name', 'image', 'text',
                  'cooking_time', 'tags', 'ingredients')
