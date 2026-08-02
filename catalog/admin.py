from django.contrib import admin

from catalog.models import Category, Contact, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройки отображения категорий в админке."""

    list_display = ("id", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Настройки отображения товаров в админке."""

    list_display = ("id", "name", "price", "category")
    list_filter = ("category",)
    search_fields = ("name", "description")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Настройки отображения контактов в админке."""

    list_display = ("id", "country", "inn", "address")
