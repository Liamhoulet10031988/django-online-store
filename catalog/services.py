"""Сервисные функции приложения каталога."""

from catalog.models import Category, Product


def get_products_by_category(category: Category):
    """Возвращает товары указанной категории в порядке их создания."""
    return Product.objects.filter(category=category).order_by("pk")
