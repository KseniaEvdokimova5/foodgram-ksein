import base64
from djoser import serializers as djoser_serializers

from django.core.files.base import ContentFile
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from recipes.models import (User, Subscriber, IngredientRecipe, Recipe,
                            Ingredient, Favorite, ShoppingCart)


class Base64ImageField(serializers.ImageField):
    """Поле для кодирования изображения в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(djoser_serializers.UserSerializer):
    """Сериализатор для модели пользователя со статусом подписки и аватаром."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_is_subscribed(self, subscribe_target):
        request = self.context.get('request')
        return False if not request or request.user.is_anonymous \
            else Subscriber.objects.filter(
            user=request.user, subscribed_to=subscribe_target
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, avatar_image):
        if not avatar_image:
            raise serializers.ValidationError('Avatar image is required.')
        return avatar_image

class IngredientInRecipeSerializer(serializers.Serializer):
    """Сериализатор ингредиентов при создании рецептов."""

    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField(min_value=1)


class SaveRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()

    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'name', 'image',
                  'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one ingredient is required.'
            )

        ingredient_ids = {item['ingredient']['id'] for item in value}

        if len(ingredient_ids) != len(value):
            raise serializers.ValidationError('Ingredients must be unique.')

        return value

    def _update_ingredients(self, recipe, ingredients_data):
        """Обновление ингредиентов для данного рецепта"""

        with transaction.atomic():
            recipe.ingredients_in_recipe.all().delete()
            IngredientRecipe.objects.bulk_create(
                IngredientRecipe(
                    recipe=recipe,
                    ingredient_id=ingredient['ingredient']['id'],
                    amount=ingredient['amount'])
                for ingredient in ingredients_data
            )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        self._update_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для считывания ингредиентов в рецептах."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения деталей рецепта."""

    author = UserSerializer()
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='ingredients_in_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return False if not request or request.user.is_anonymous \
            else Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return False if not request or request.user.is_anonymous \
            else ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeBriefSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для пользователя с его рецептами и данными о подписке."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count',
                  'avatar')
        #read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        recipes = obj.recipes.all()

        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeBriefSerializer(recipes, many=True, context=self.context).data
