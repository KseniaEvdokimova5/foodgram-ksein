import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from backend_foodgram.settings import CSV_FILES_DIR


class Command(BaseCommand):
    help = 'Загружает данные из файла ingredients.csv в Postgres'

    def handle(self, *args, **options):
        csv_file = 'ingredients.csv'
        csv_path = Path(CSV_FILES_DIR) / csv_file
        fieldnames = ['name', 'measurement_unit']
        ingredients = []

        try:
            with open(csv_path, encoding='utf-8') as f:
                created = Ingredient.objects.bulk_create(
                    [Ingredient(**row) for row in csv.DictReader(f, fieldnames)],
                    ignore_conflicts=True
                )
                print(f'Данные загружены: {len(created)}')
        except Exception as e:
            print('Произошла неожиданная ошибка в файле {csv_file}: ', e)

