from django.contrib.auth import get_user_model
from django.db.models import Count
from djoser.serializers import UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from django.db import transaction

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, Favorite, ShoppingCart
from user.models import Follow

User = get_user_model()


class IsSubscribedMethod:
    def get_is_subscribed(self, request, obj):
        if request and request.user.is_authenticated:
            if isinstance(obj, User):
                return request.user.sub_user.filter(author=obj).exists()
            return True
        return False


class UserReadSerializer(UserSerializer, IsSubscribedMethod):
    """Сериализатор для модели User."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            return IsSubscribedMethod().get_is_subscribed(request, obj)
        return False


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
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            return serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )
        return value


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

        recipe_name, recipe_text = data['name'], data['text']
        ingredient_amount = data['ingredients']
        if not ingredient_amount:
            raise serializers.ValidationError(
                'Рецепт не может быть создан без ингредиентов.'
            )
        list_of_ingredients = set()
        for value in ingredient_amount:
            ingredient_id = value.get('id')

            if not Ingredient.objects.filter(pk=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id={ingredient_id} не существует.'
                )
            ingredient_obj = Ingredient.objects.get(pk=ingredient_id)
            if ingredient_obj in list_of_ingredients:
                raise serializers.ValidationError(
                    'Рецепт не может иметь двух одиноковых ингредиентов.',
                )
            list_of_ingredients.add(ingredient_obj)
        recipe = Recipe.objects.filter(
            name=recipe_name, text=recipe_text).exists()
        if recipe:
            raise serializers.ValidationError(
                f'Данный рецепт "{recipe_name}" уже существует.'
            )
        return data
    
    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )

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

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


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
        if request and request.user.is_authenticated:
            return request.user.favorite_recipe.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.shopping_cart.filter(recipe=obj).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer,
                             IsSubscribedMethod):
    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            return IsSubscribedMethod().get_is_subscribed(request, obj)
        return False

    def get_recipes(self, obj):
        request = self.context['request']
        recipe_limit = request.GET.get('recipes_limit')
        if recipe_limit:
            recipes = obj.recipe.all()[:int(recipe_limit)]
        else:
            recipes = obj.recipe.all()
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

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в избранное")
        return attrs


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в корзину покупок")
        return attrs


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('author',)

    def validate_author(self, value):
        request = self.context.get('request')
        user = request.user
        if value == user:
            raise serializers.ValidationError('Вы не можете подписаться на себя')
        if Follow.objects.filter(user=user, author=value).exists():
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']
        subscription = Follow.objects.create(user=user, author=author)
        return subscription
