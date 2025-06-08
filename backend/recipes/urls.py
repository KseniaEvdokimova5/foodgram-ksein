from django.urls import path
from .views import short_link_recipe

urlpatterns = [
    path('link/<int:id>', short_link_recipe, name='resolve-short-link'),
]