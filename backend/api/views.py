from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)

from .constants import NO_EXIST_SUB, RECIPE_NOT_ADD, SHOPPING_CART_NAME
from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePaginator
from .pdf_generator import download_pdf_shopping_cart
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscriptionCreateSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserReadSerializer)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = RecipePaginator

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create_favorite_or_cart(self, serializer_class, pk, request):
        user = request.user
        data = {'user': user.id, 'recipe': pk}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorite_or_cart(self, model, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        queryset = model.objects.filter(user=user, recipe=recipe)
        deleted_count, _ = queryset.delete()
        if deleted_count == 0:
            return Response(
                {'message': RECIPE_NOT_ADD},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients_list = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name', 'ingredient__measurement_unit')

        buffer = download_pdf_shopping_cart(request.user, ingredients_list)
        filename = f'{request.user.username}\'s-{SHOPPING_CART_NAME}'
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        serializer_class = ShoppingCartSerializer
        return self.create_favorite_or_cart(serializer_class, pk, request)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        model = ShoppingCart
        return self.delete_favorite_or_cart(model, pk, request)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_name='favorite'
    )
    def favorite(self, request, pk):
        serializer_class = FavoriteSerializer
        return self.create_favorite_or_cart(serializer_class, pk, request)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        model = Favorite
        return self.delete_favorite_or_cart(model, pk, request)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = RecipePaginator

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        user = self.request.user
        queryset = User.objects.filter(sub_author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_name='subscribe'
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        data = {'user': user.id, 'author': pk}
        serializer = SubscriptionCreateSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        subscription = user.sub_user.filter(author=author)
        deleted_count, _ = subscription.delete()
        if deleted_count == 0:
            return Response(
                {'message': NO_EXIST_SUB},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
