from django_filters.rest_framework import filters, FilterSet

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_by_favorite',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    def filter_by_favorite(self, recipes_queryset, name, value):
        return self._filter_by_user_relation(recipes_queryset, 'favorites', value)

    def filter_by_shopping_cart(self, recipes_queryset, name, value):
        return self._filter_by_user_relation(recipes_queryset, 'shopping_cart_items', value)

    def _filter_by_user_relation(self, recipes_queryset, related_name, value):
        if value and self.request.user.is_authenticated:
            return recipes_queryset.filter(
                **{f"{related_name}__user": self.request.user}
            )

        return recipes_queryset
