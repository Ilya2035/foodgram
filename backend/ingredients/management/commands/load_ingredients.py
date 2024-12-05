import json
from django.core.management.base import BaseCommand
from ingredients.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к JSON-файлу с ингредиентами')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            ingredients = [
                Ingredient(name=item['name'], measurement_unit=item['measurement_unit'])
                for item in data
            ]
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка при загрузке ингредиентов: {e}'))
