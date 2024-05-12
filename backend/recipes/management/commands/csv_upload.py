import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


def ingredient_create(row):
    return Ingredient(
        name=row[0],
        measurement_unit=row[1]
    )


action = {
    'ingredients.csv': ingredient_create
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        path = str(settings.BASE_DIR.joinpath('data').resolve()) + '/'
        ingredients_to_create = []
        
        for key, create_function in action.items():
            with open(path + key, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    ingredient = create_function(row)
                    ingredients_to_create.append(ingredient)
        
        Ingredient.objects.bulk_create(ingredients_to_create)
