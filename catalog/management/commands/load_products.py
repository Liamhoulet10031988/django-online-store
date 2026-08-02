from django.core.management import call_command
from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    """Загружает тестовые категории и товары из фикстуры."""

    help = "Удаляет старые данные и загружает тестовые товары"

    def handle(self, *args, **options) -> None:
        """Удаляет старые записи и загружает фикстуру."""
        Product.objects.all().delete()
        Category.objects.all().delete()

        call_command("loaddata", "catalog_data.json", verbosity=0)

        self.stdout.write(
            self.style.SUCCESS("Тестовые данные успешно загружены")
        )
