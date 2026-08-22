from contextlib import redirect_stdout
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalog.admin import CategoryAdmin, ContactAdmin, ProductAdmin
from catalog.models import Category, Contact, Product


class CategoryModelTest(TestCase):
    """Тесты модели категории."""

    def test_category_creation(self) -> None:
        category = Category.objects.create(
            name="Смартфоны",
            description="Мобильные телефоны",
        )

        self.assertEqual(category.name, "Смартфоны")
        self.assertEqual(str(category), "Смартфоны")
        self.assertEqual(Category._meta.verbose_name, "Категория")
        self.assertEqual(Category._meta.verbose_name_plural, "Категории")


class ProductModelTest(TestCase):
    """Тесты модели товара."""

    def test_product_creation(self) -> None:
        category = Category.objects.create(name="Ноутбуки")
        product = Product.objects.create(
            name="MacBook Air",
            description="Ноутбук Apple",
            category=category,
            price=150000,
        )

        self.assertEqual(product.category, category)
        self.assertEqual(product.category_id, category.pk)
        self.assertFalse(product.is_published)
        self.assertIsNone(product.owner)
        self.assertEqual(str(product), "MacBook Air")
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)

    def test_related_products(self) -> None:
        category = Category.objects.create(name="Смартфоны")
        product = Product.objects.create(
            name="iPhone 15",
            category=category,
            price=120000,
        )

        self.assertEqual(list(category.products.all()), [product])


class ContactModelTest(TestCase):
    """Тесты модели контактов."""

    def test_contact_string(self) -> None:
        contact = Contact.objects.create(
            country="Россия",
            inn="1234567890",
            address="Москва",
        )

        self.assertEqual(str(contact), "Россия: Москва")


class AdminTest(TestCase):
    """Тесты настроек административной панели."""

    def test_category_admin_settings(self) -> None:
        self.assertEqual(CategoryAdmin.list_display, ("id", "name"))

    def test_product_admin_settings(self) -> None:
        self.assertEqual(
            ProductAdmin.list_display,
            (
                "id",
                "name",
                "price",
                "category",
                "is_published",
                "owner",
            ),
        )
        self.assertEqual(
            ProductAdmin.list_filter,
            ("category", "is_published"),
        )
        self.assertEqual(
            ProductAdmin.search_fields,
            ("name", "description"),
        )

    def test_contact_admin_settings(self) -> None:
        self.assertEqual(
            ContactAdmin.list_display,
            ("id", "country", "inn", "address"),
        )


class ViewsTest(TestCase):
    """Тесты страниц интернет-магазина."""

    def setUp(self) -> None:
        self.category = Category.objects.create(name="Тестовая категория")

        for number in range(6):
            Product.objects.create(
                name=f"Товар {number}",
                category=self.category,
                price=1000 + number,
            )

    def test_home_page_returns_products(self) -> None:
        response = self.client.get(reverse("catalog:home"))

        products = list(response.context["products"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(products), 6)
        self.assertEqual(products[0].name, "Товар 0")

    def test_contacts_page_contains_database_contacts(self) -> None:
        Contact.objects.create(
            country="Россия",
            inn="1234567890",
            address="Москва",
        )

        response = self.client.get(reverse("catalog:contacts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Россия")
        self.assertContains(response, "1234567890")
        self.assertContains(response, "Москва")

    def test_contacts_form_accepts_post_request(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            response = self.client.post(
                reverse("catalog:contacts"),
                {
                    "name": "Лев",
                    "phone": "+7 900 000-00-00",
                    "message": "Тестовое сообщение",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Спасибо, Лев!")
        self.assertIn("Телефон: +7 900 000-00-00", output.getvalue())


class FixtureAndCommandTest(TestCase):
    """Тесты фикстуры и команды загрузки данных."""

    def test_fixture_loads_categories_and_products(self) -> None:
        call_command("loaddata", "catalog_data.json", verbosity=0)

        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Product.objects.count(), 5)
        self.assertEqual(
            Product.objects.get(name="iPhone 15").category.name,
            "Смартфоны",
        )

    def test_load_products_replaces_old_data(self) -> None:
        old_category = Category.objects.create(name="Старая категория")
        Product.objects.create(
            name="Старый товар",
            category=old_category,
            price=100,
        )
        output = StringIO()

        call_command("load_products", stdout=output)

        self.assertFalse(
            Category.objects.filter(name="Старая категория").exists()
        )
        self.assertFalse(Product.objects.filter(name="Старый товар").exists())
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Product.objects.count(), 5)
        self.assertIn("Тестовые данные успешно загружены", output.getvalue())
