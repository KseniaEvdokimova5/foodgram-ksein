from django.contrib import admin
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, IngredientRecipe, Recipe, ShoppingCart,
    Subscriber, User
)

@admin.register(User)
class AdminUser(UserAdmin):
    list_display = [
        'id', 'username', 'full_name',
        'email', 'preview', 'recipes_count',
        'subscriptions_count', 'subscribers_count'
    ]
    search_fields = ['id', 'username', 'full_name', 'email']
    list_filter = ['is_active', 'is_superuser']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            recipes_count=Count("recipes"),
            subscriptions_count=Count("subscribers"),
            subscribers_count=Count("subscriptions_of")
        )
        return queryset

    @admin.display(description='Картинка')
    def preview(self, user):
        if user.avatar:
            return mark_safe(f'<img src="{user.avatar.url}" style="max-height: 64px;">')
        
        return ""

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='В рецептах')
    def recipes_count(self, user):
        return user.recipes_count

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions_count

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers_count


@admin.register(Subscriber)
class AdminSubscription(admin.ModelAdmin):
    list_display = ['user', 'subscribed_to']
    search_fields = ['user__username', 'subscribed_to__username']


admin.site.unregister(Group)


@admin.register(Ingredient)
class AdminIngredient(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit', 'recipes_count']
    search_fields = ['name', 'measurement_unit']
    list_filter = ['measurement_unit']
    ordering = ['name']

    @admin.display(description='В рецептах')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(IngredientRecipe)
class AdminIngredientRecipe(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
    search_fields = ['recipe__name', 'ingredient__name']


@admin.register(Favorite)
class AdminFavorite(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    search_fields = ['user__username', 'recipe__name']


@admin.register(Recipe)
class AdminRecipe(admin.ModelAdmin):
    list_display = ['id', 'name', 'cooking_time', 'author', 'favorites', 'products', 'preview']
    search_fields = ['name', 'author__username']
    list_filter = ['author']
    date_hierarchy = 'pub_date'

    @admin.display(description='В избранном')
    def favorites(self, instance):
        return instance.favorites.count()

    @admin.display(description='Продукты')
    def products(self, instance):
        ingredients_data = [f'{ingredient_in_recipe.ingredient.name} - {ingingredient_in_reciperedient.ingredient.measurement_unit}{ingredient_in_recipe.amount}' for ingredient_in_recipe in instance.ingredients_in_recipe.all()]

        return mark_safe('<br />'.join(ingredients_data))

    @admin.display(description='Картинка')
    def preview(self, instance):
        if instance.image:
            return mark_safe(f'<img src="{instance.image.url}" style="max-height: 64px;">')
        
        return ""


@admin.register(ShoppingCart)
class AdminShoppingCart(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    search_fields = ['user__username', 'recipe__name']
