from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from user.models import Follow

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.sub_user.filter(author=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.
    Только GET запросы.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на запись."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(
        max_length=None,
        use_url=True
    )
    ingredients = IngredientAmountSerializer(
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'text'),
                message='Данный рецепт уже существует.'
            )
        ]

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен иметь хотя бы 1 тэг.'
            )
        unique_tags = set(value)
        if len(unique_tags) != len(value):
            raise serializers.ValidationError(
                'Рецепт не может содержать повторяющиеся теги.'
            )
        return value

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'Поле `ingredients` обязательно для заполнения.'
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                'Поле `tags` обязательно для заполнения.'
            )

        ingredient_amount = data['ingredients']
        if not ingredient_amount:
            raise serializers.ValidationError(
                'Рецепт не может быть создан без ингредиентов.'
            )
        list_of_ingredients = set()
        for value in ingredient_amount:
            ingredient = value.get('id')

            if ingredient not in Ingredient.objects.all():
                raise serializers.ValidationError(
                    f'Ингредиент "{ingredient}" не существует.'
                )
            if ingredient in list_of_ingredients:
                raise serializers.ValidationError(
                    'Рецепт не может иметь двух одинаковых ингредиентов.',
                )
            list_of_ingredients.add(ingredient)
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredients_to_create = []
        for ingredient_data in ingredients:
            ingredient = ingredient_data['id']
            amount = ingredient_data['amount']
            ingredients_to_create.append(
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount
                )
            )
        IngredientRecipe.objects.bulk_create(ingredients_to_create)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        validated_data['author'] = author
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients)
        instance.tags.set(tags)
        return super().update(instance, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на чтение."""
    author = UserReadSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = TagSerializer(
        many=True, read_only=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True, source='recipe'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'tags', 'author', 'ingredients', 'image',
            'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.favorite_recipe.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.shopping_cart.filter(recipe=obj).exists()
        )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context['request']
        recipe_limit = request.GET.get('recipes_limit')
        if recipe_limit:
            recipes = obj.recipes.all()[:int(recipe_limit)]
        else:
            recipes = obj.recipes.all()
        serializer = ShortRecipeSerializer(
            recipes, many=True, context={'request': request}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        results = Recipe.objects.filter(author=obj).aggregate(
            count_recipes=Count('name')
        )
        return results['count_recipes']


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(
            instance.recipe,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину покупок'
            )
        ]

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(
            instance.recipe,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('author', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('author', 'user'),
                message='Вы уже подписаны на этого пользователя',
            )
        ]

    def validate_author(self, value):
        request = self.context.get('request')
        user = request.user
        if value == user:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )
        return value
