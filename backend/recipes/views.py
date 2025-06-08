from django.shortcuts import get_object_or_404, redirect

from .models import Recipe

def short_link_recipe(request, id):
    recipe = get_object_or_404(Recipe, pk=id)
    return redirect(
        request.build_absolute_uri('/') + f'recipes/{recipe.id}/'
    )