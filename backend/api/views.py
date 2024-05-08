from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from user.models import Follow, MyUser

from .constants import (DOUBLE_SUB, NO_EXIST_SUB, RECIPE_ALREADY_EXISTS,
                        RECIPE_NOT_ADD, RECIPE_NOT_FOUND, SELF_SUB,
                        SHOPPING_CART_NAME)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthenticatedCustom, IsOwnerAdminOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          TagSerializer)
from .utils import download_pdf_shopping_cart


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def favorite_or_shopping_cart(self, model, pk, request):
        user = request.user

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'message': RECIPE_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = model.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if queryset.exists():
                return Response(
                    {'message': RECIPE_ALREADY_EXISTS},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            model.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not queryset.exists():
                return Response(
                    {'message': RECIPE_NOT_ADD},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        user = request.user
        buffer = download_pdf_shopping_cart(user)
        filename = f'{user.username}\'s-{SHOPPING_CART_NAME}'
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        model = ShoppingCart
        return self.favorite_or_shopping_cart(
            model, pk, request
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='favorite'
    )
    def favorite(self, request, pk):
        model = Favorite
        return self.favorite_or_shopping_cart(
            model, pk, request
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    queryset = MyUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        user = self.request.user
        queryset = MyUser.objects.filter(sub_author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='subscribe'
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(MyUser, pk=id)
        subscription = user.sub_user.filter(author=author)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'message': SELF_SUB},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if subscription.exists():
                return Response(
                    {'message': DOUBLE_SUB},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not subscription:
                return Response(
                    {'message': NO_EXIST_SUB},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticatedCustom,),
        url_name='me'
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
