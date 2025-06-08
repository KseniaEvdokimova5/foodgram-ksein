import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from backend_foodgram.settings import JSON_FILES_DIR


class Command(BaseCommand):
    help = 'Загружает данные из файла ingredients.json в Postgres'

    def handle(self, *args, **options):
        json_file = 'ingredients.json'
        json_path = Path(JSON_FILES_DIR) / json_file
        fieldnames = ['name', 'measurement_unit']
        ingredients = []

        try:
            with open(json_path, encoding='utf-8') as f:
                created = Ingredient.objects.bulk_create([Ingredient(**row) for row in json.load(f)], ignore_conflicts=True)
                print(f'Данные загружены: {len(created)}')

        except FileNotFoundError as fe:
            print(f"Файл не найден {csv_file}:", fe)
        except Exception as e:
            print(f'Произошла неожиданная ошибка при загрузке из файла {json_file}: ', e)
