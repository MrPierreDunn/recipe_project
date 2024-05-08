from django.db.models import Count
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from user.models import MyUser


class IsSubscribedMethod:
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            if isinstance(obj, MyUser):
                return user.sub_user.filter(author=obj).exists()
            return True
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = MyUser
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'password'
        )


class CustomUserSerializer(UserSerializer, IsSubscribedMethod):
    """Сериализатор для модели User."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MyUser
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed'
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
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

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
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id', 'author')

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 1 мин.'
            )
        return value

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
        list_of_ingredients = []
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
            list_of_ingredients.append(ingredient_obj)

            amount = value['amount']
            if not isinstance(amount, int):
                error_message = amount.detail[0]
                raise serializers.ValidationError(
                    error_message
                )
        recipe = Recipe.objects.filter(
            name=recipe_name, text=recipe_text).exists()
        if recipe:
            raise serializers.ValidationError(
                f'Данный рецепт "{recipe_name}" уже существует.'
            )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        cooking_time = validated_data.get('cooking_time')
        if not cooking_time:
            raise serializers.ValidationError(
                'Поле `cooking_time` обязательно для заполнения.'
            )

        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()

            for ingredient in ingredients:
                ingredient_id = ingredient['id']
                amount = ingredient['amount']
                IngredientRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_id,
                    amount=amount
                )

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags)

        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на чтение."""
    author = CustomUserSerializer(
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
        user = self.context['request'].user
        if user.is_authenticated:
            return user.favorite_recipe.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
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
        model = MyUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

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
