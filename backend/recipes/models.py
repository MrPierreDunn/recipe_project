from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.settings import MAX_LEN_TITLE
from user.models import MyUser

from .constants import MAX_AMOUNT, MIN_AMOUNT


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(
        max_length=16,
        unique=True,
        verbose_name='Имя тэга',
        help_text='Введите имя тэга',
    )
    color = ColorField(
        max_length=7,
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
        indexes = [
            models.Index(
                fields=('name',), name='tag_name_idx'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LEN_TITLE]


class Ingredient(models.Model):
    """Модель для ингредиентов."""
    name = models.CharField(
        max_length=200,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        indexes = [
            models.Index(
                fields=('name',), name='ingredient_name_idx'
            )
        ]
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_with_measurement_unit'
            ),
        ]

    def __str__(self):
        return self.name[:MAX_LEN_TITLE]


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
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг'
    )
    author = models.ForeignKey(
        MyUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipe'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='Избранное',
        help_text=(
            'Поставьте галочку, чтобы'
            ' добавить рецепт в избранное.'
        ),
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
        verbose_name='Список покупок',
        help_text=(
            'Поставьте галочку, чтобы'
            ' добавить рецепт в список покупок.'
        ),
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1, 'Время готовки не может быть меньше минуты.')
        ],
        verbose_name='Время приготовления'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at', )
        indexes = [
            models.Index(
                fields=('name',), name='recipe_name_idx'
            ),
            models.Index(
                fields=('author',), name='recipe_author_idx'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LEN_TITLE]


class Favorite(models.Model):
    """Модель для избранных рецептов."""
    user = models.ForeignKey(
        MyUser,
        related_name='favorite_recipe',
        on_delete=models.CASCADE,
        verbose_name='Понравившийся рецепт',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipe',
        on_delete=models.CASCADE,
        verbose_name='Понравившийся рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        f'Пользователь с именем {self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(models.Model):
    """
    Модель для списка покупок пользователя.
    Связь пользователя и рецепта в списке покупок.
    """
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        help_text='Выберите пользователя',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт для покупок',
        help_text='Выберите рецепт для списка покупок',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        f'Пользователь {self.author} добавил {self.recipe} в список покупок.'
