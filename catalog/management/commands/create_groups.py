from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создаёт учебные группы и назначает им права доступа."""

    help = "Создаёт группы модераторов продуктов и контент-менеджеров"

    def handle(self, *args, **options) -> None:
        """Создаёт группы и связывает их с разрешениями."""
        moderator_group, _ = Group.objects.get_or_create(
            name="Модератор продуктов"
        )
        can_unpublish_product = Permission.objects.get(
            codename="can_unpublish_product",
            content_type__app_label="catalog",
        )
        delete_product = Permission.objects.get(
            codename="delete_product",
            content_type__app_label="catalog",
        )
        moderator_group.permissions.add(
            can_unpublish_product,
            delete_product,
        )

        content_manager_group, _ = Group.objects.get_or_create(
            name="Контент-менеджер"
        )
        add_blog = Permission.objects.get(
            codename="add_blog",
            content_type__app_label="blog",
        )
        change_blog = Permission.objects.get(
            codename="change_blog",
            content_type__app_label="blog",
        )
        delete_blog = Permission.objects.get(
            codename="delete_blog",
            content_type__app_label="blog",
        )
        content_manager_group.permissions.add(
            add_blog,
            change_blog,
            delete_blog,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Группы и права доступа успешно созданы"
            )
        )
