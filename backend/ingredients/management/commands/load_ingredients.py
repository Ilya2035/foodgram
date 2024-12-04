import csv
from django.core.management.base import BaseCommand
from ingredients.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='The relative path to the CSV file (e.g., data/ingredient.csv)'
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, fieldnames=['name', 'measurement_unit'])
                for row in reader:
                    Ingredient.objects.get_or_create(
                        name=row['name'],
                        measurement_unit=row['measurement_unit']
                    )
            self.stdout.write(self.style.SUCCESS('Ingredients have been loaded successfully.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error loading ingredients: {e}'))
