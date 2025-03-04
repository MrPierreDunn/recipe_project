from django.conf import settings
from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


class RecipeIngredientAdmin(admin.StackedInline):
    model = IngredientRecipe
    autocomplete_fields = ('ingredient',)


@admin.register(IngredientRecipe)
class RecipeIngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')
    list_display_links = ('ingredient', 'recipe')
    list_editable = ('amount',)
    search_fields = ('ingredients', 'recipe')
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('id', 'user')
    search_fields = ('user',)
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'get_ingredients',
        'get_tags', 'get_count_recipe_in_favorites',

    )
    list_filter = ('name', 'author', 'tags')
    list_display_links = ('name',)
    search_fields = (
        'name', 'cooking_time', 'author__username',
        'ingredients__name'
    )
    inlines = (RecipeIngredientAdmin,)
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL

    @admin.display(description='Игредиенты')
    def get_ingredients(self, obj):
        ingredients = [
            ingredient.name for ingredient in obj.ingredients.all()
        ]
        return ', '.join(ingredients)

    @admin.display(description='Количество данного рецепта в избранном')
    def get_count_recipe_in_favorites(self, obj):
        return obj.favorite_recipe.count()

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        tags = [
            tag.name for tag in obj.tags.all()
        ]
        return ', '.join(tags)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)
    list_editable = ('name', 'color', 'slug')
    search_fields = ('name', 'slug', 'color')
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL
