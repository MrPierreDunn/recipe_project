from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from .constants import (INGREDIENT_RECIPE_LIMIT, MAX_AMOUNT, MIN_AMOUNT,
                        TAG_COLOR_LIMIT, TAG_NAME_LIMIT)

User = get_user_model()


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(
        max_length=TAG_NAME_LIMIT,
        unique=True,
        verbose_name='Имя тэга',
        help_text='Введите имя тэга',
        db_index=True,
    )
    color = ColorField(
        max_length=TAG_COLOR_LIMIT,
        unique=True,
        default='#F29C1B',
        verbose_name='Цвет',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор для формирования ссылки'
            ' разрешены символы латиницы,'
            ' цифры, дефис и подчеркивание.'
        ),
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:settings.MAX_LEN_TITLE]


class Ingredient(models.Model):
    """Модель для ингредиентов."""
    name = models.CharField(
        max_length=INGREDIENT_RECIPE_LIMIT,
        verbose_name='Ингредиент',
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_RECIPE_LIMIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_with_measurement_unit'
            ),
        ]

    def __str__(self):
        return self.name[:settings.MAX_LEN_TITLE]


class IngredientRecipe(models.Model):
    """Модель для связи Ingredient и Recipe."""
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        help_text='Выберите ингредиент',
    )
    recipe = models.ForeignKey(
        'Recipe',
        related_name='recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        help_text='Укажите количество выбранного ингредиента',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                f'Минимальное количество ингредиента - {MIN_AMOUNT}'
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                f'Максимальное количество ингредиента - {MAX_AMOUNT}'
            )
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_for_recipe')
        ]

    def __str__(self):
        return self.amount


class Recipe(models.Model):
    """Модель для рецептов."""
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено',
    )
    name = models.CharField(
        max_length=INGREDIENT_RECIPE_LIMIT,
        verbose_name='Название рецепта',
        db_index=True,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        db_index=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        null=False,
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                f'Минимальное время готовки - {MIN_AMOUNT}'
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                f'Максимальное время готовки - {MAX_AMOUNT}'
            )
        ],
        verbose_name='Время приготовления'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at', )

    def __str__(self):
        return self.name[:settings.MAX_LEN_TITLE]


class BaseRecipeRelation(models.Model):
    """
    Базовая абстрактная модель для связей с рецептами.
    Содержит общие поля и настройки.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Выберите пользователя',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )

    class Meta:
        abstract = True


class Favorite(BaseRecipeRelation):
    """Модель для избранных рецептов."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite_recipe'

    def __str__(self):
        f'Пользователь с именем {self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(BaseRecipeRelation):
    """
    Модель для списка покупок пользователя.
    Связь пользователя и рецепта в списке покупок.
    """

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        f'Пользователь {self.author} добавил {self.recipe} в список покупок.'
