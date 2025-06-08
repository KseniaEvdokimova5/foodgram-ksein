from django.urls import path, include
from rest_framework import routers

from .views import (
    UsersViewSet, RecipesViewSet, IngredientsViewSet
)

router = routers.SimpleRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    # Конечные точки аутентификации
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]

urlpatterns += router.urls