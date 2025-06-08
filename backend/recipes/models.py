from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Upper
from django.core.validators import (
    MinValueValidator, MaxValueValidator,
    RegexValidator, EmailValidator
)
from django.db import models

class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z'
            )
        ],
        verbose_name='Имя пользователя'
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты'
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )

    avatar = models.ImageField(
        upload_to='images/avatar/',
        verbose_name='Аватар',
        null=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = [Upper('email')]
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return (f"{self.username}, {self.email}, "
                f"{self.first_name}, {self.last_name}")


class Subscriber(models.Model):
    """Модель подписчиков"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчики'
    )

    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_of',
        verbose_name='Подписки'
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user}, {self.subscribed_to}'


class Ingredient(models.Model):
    """Модель продукта"""

    name = models.CharField(
        max_length=128,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('-name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )

    image = models.ImageField(
        upload_to='images/recipes/',
        verbose_name='Картинка блюда',
        null=False
    )

    text = models.TextField(
        verbose_name='Описание рецепта'
    )

    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='IngredientRecipe',
        verbose_name='Список продуктов'
    )

    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(limit_value=1)],
        verbose_name='Время приготовления в минутах'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = "recipes"

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Промежуточная модель для Ingredient и Recipe при many-to-many"""

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт'
    )

    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(limit_value=1)
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Продукты в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        default_related_name = 'ingredients_in_recipe'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient}, {self.recipe}, {self.amount}'


class Favorite(models.Model):
    """Модель избранного"""

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Избранное пользователя'
    )

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном пользователя'
    )

    class Meta:
        verbose_name = 'Избранное пользователя'
        verbose_name_plural = 'Избранное пользователя'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.recipe}, {self.user}'


class ShoppingCart(models.Model):
    """Модель списка покупок пользователя"""

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Список покупок пользователя'
    )

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart_items'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart'
            )
        ]

    def __str__(self):
        return f'{self.recipe}, {self.user}'
