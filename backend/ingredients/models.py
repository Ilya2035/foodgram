from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        return self.name
