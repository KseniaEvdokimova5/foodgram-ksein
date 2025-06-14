# Generated by Django 5.2.1 on 2025-06-07 19:33

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'verbose_name': 'Продукт', 'verbose_name_plural': 'Продукты'},
        ),
        migrations.AlterModelOptions(
            name='ingredientrecipe',
            options={'verbose_name': 'Продукты в рецепте', 'verbose_name_plural': 'Продукты в рецептах'},
        ),
        migrations.RemoveField(
            model_name='favorite',
            name='add_time',
        ),
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1), django.core.validators.MaxValueValidator(limit_value=6000)], verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='recipes.ingredient', verbose_name='Продукт'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1), django.core.validators.MaxValueValidator(limit_value=1000)], verbose_name='Время приготовления в минутах'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(through='recipes.IngredientRecipe', to='recipes.ingredient', verbose_name='Список продуктов'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(error_messages={'unique': 'Вводимая электронная почта уже зарегистрирована.'}, max_length=254, unique=True, validators=[django.core.validators.EmailValidator(message='Введите валидную электронную почту, например "name@domain.com".')], verbose_name='Адрес электронной почты'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(message='Имя пользователя на латинице', regex='^[\\w.@+-]+\\Z')]),
        ),
    ]
