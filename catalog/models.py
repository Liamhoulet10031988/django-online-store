from django.conf import settings
from django.db import models


class Category(models.Model):
    """Категория товаров интернет-магазина."""

    name = models.CharField(max_length=100, verbose_name="Наименование")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )

    def __str__(self) -> str:
        """Возвращает наименование категории."""
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(models.Model):
    """Товар интернет-магазина."""

    name = models.CharField(max_length=100, verbose_name="Наименование")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
    )
    price = models.PositiveIntegerField(verbose_name="Цена за покупку")
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего изменения",
    )

    def __str__(self) -> str:
        """Возвращает наименование товара."""
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        permissions = [
            (
                "can_unpublish_product",
                "Может отменять публикацию товара",
            ),
        ]


class Contact(models.Model):
    """Контактные данные интернет-магазина."""

    country = models.CharField(max_length=100, verbose_name="Страна")
    inn = models.CharField(max_length=30, verbose_name="ИНН")
    address = models.CharField(max_length=255, verbose_name="Адрес")

    def __str__(self) -> str:
        """Возвращает страну и адрес контакта."""
        return f"{self.country}: {self.address}"

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
