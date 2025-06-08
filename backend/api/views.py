from django.http import HttpResponse, FileResponse
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Ingredient, IngredientRecipe, Recipe,
    Favorite, ShoppingCart, User, Subscriber
)
from .filters import RecipeFilter
from .permissions import IsOwnOrReadOnly
from .serializers import (
    AvatarSerializer, SaveRecipeSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeBriefSerializer,
    UserSubscriptionSerializer
)
from .pagination import DefaultPageNumberPagination

import datetime


class UsersViewSet(ViewSet):
    @action(methods=['put'], detail=False, permission_classes=[permissions.IsAuthenticated],
            url_path='me/avatar', url_name='avatar')
    def change_avatar(self, request):
        serializer = AvatarSerializer(request.user,
                                      data=request.data, partial=True,
                                      context={'request': request})

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @change_avatar.mapping.delete
    def remove_avatar(self, request):
        if not request.user.avatar:
            return Response({'detail': 'No avatar to delete.'},
                            status=status.HTTP_400_BAD_REQUEST)

        request.user.avatar.delete(save=True)
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        users = User.objects.filter(subscriptions_of__user=request.user)
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(users, request)
        serializer = UserSubscriptionSerializer(page, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        user_to_subscribe = get_object_or_404(User, id=pk)

        if request.user == user_to_subscribe:
            raise serializers.ValidationError(
                'Cannot subscribe to yourself.')

        _, created = Subscriber.objects.get_or_create(
            user=request.user,
            subscribed_to=user_to_subscribe
        )
        if not created:
            raise serializers.ValidationError(
                f'Already subscribed to {user_to_subscribe.username}.'
            )
        
        serializer = UserSubscriptionSerializer(user_to_subscribe, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        deleted_count, _ = Subscriber.objects.filter(
            user=request.user, subscribed_to_id=pk
        ).delete()

        if deleted_count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)

class RecipesViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = DefaultPageNumberPagination

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return RecipeReadSerializer
            case 'retrieve':
                return RecipeReadSerializer
            case 'create':
                return SaveRecipeSerializer
            case 'update':
                return SaveRecipeSerializer
            case 'partial_update':
                return SaveRecipeSerializer
            case default:
                return RecipeBriefSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'update':
            permission_classes = [IsOwnOrReadOnly]
        elif self.action == 'partial_update':
            permission_classes = [IsOwnOrReadOnly]
        elif self.action == 'destroy':
            permission_classes = [IsOwnOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Возвращает оптимизированный QuerySet."""

        return Recipe.objects.all().select_related('author').prefetch_related('ingredients_in_recipe')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe_to_list(self, request, list_class, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = list_class.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                f'Recipe "{recipe.name}" is already in {list_class._meta.verbose_name.title()}.'
            )

        serializer = RecipeBriefSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from_list(self, request, list_class, pk=None):
        deleted_count, _ = list_class.objects.filter(
            user=request.user, recipe_id=pk
        ).delete()
        if deleted_count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True, permission_classes=[permissions.AllowAny],
            url_path='get-link', url_name='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(
            {
                'short-link': request.build_absolute_uri
                (
                    reverse('resolve-short-link', args=[recipe.id])
                )
            }, 
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True, permission_classes=[permissions.IsAuthenticated],
            url_path='favorite', url_name='favorite')
    def add_favorite(self, request, pk=None):
        return self.add_recipe_to_list(request, Favorite, pk)

    @add_favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self.delete_from_list(request, Favorite, pk)

    @action(methods=['post'], detail=True, permission_classes=[permissions.IsAuthenticated],
            url_path='shopping_cart', url_name='shopping_cart')
    def add_shopping_cart(self, request, pk=None):
        return self.add_recipe_to_list(request, ShoppingCart, pk)

    @add_shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        return self.delete_from_list(request, ShoppingCart, pk)

    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart_items__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit', 'ingredient__id',
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('-ingredient__name')

        recipes = IngredientRecipe.objects.filter(
            recipe__shopping_cart_items__user=request.user
        ).values(
            'recipe__name', 'recipe__author__first_name', 'recipe__author__last_name', 'recipe__id'
        ).annotate(
            cnt=Count('*')
        ).order_by('-recipe__author__first_name')

        shopping_list = [
            f"{idx}. {item['ingredient__name'].capitalize()} ({item['ingredient__measurement_unit']}) - {item['total_amount']}"
            for idx, item in enumerate(ingredients, start=1)
        ]

        recipes_list = [
            f"{idx}. {item['recipe__name']} от {item['recipe__author__first_name'] + ' ' + item['recipe__author__last_name']}"
            for idx, item in enumerate(recipes, start=1)
        ]

        return FileResponse(
            '\n'.join([
                f'Дата отчета: {datetime.datetime.now().strftime("%d.%m.%Y")}',
                'Продукты:',
                *shopping_list,
                'Рецепты:',
                *recipes_list
            ]),
            content_type='text/plain'
        )

class IngredientsViewSet(ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
