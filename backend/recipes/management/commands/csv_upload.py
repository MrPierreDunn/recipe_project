import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


def ingredient_create(row):
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1]
    )


action = {
    'ingredients.csv': ingredient_create
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        path = str(settings.BASE_DIR.joinpath('data').resolve()) + '/'
        for key in action:
            with open(path + key, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    action[key](row)
