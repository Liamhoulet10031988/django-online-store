from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User


@shared_task
def deactivate_inactive_users():
    """Блокирует пользователей, которые не входили больше месяца."""
    inactive_before = timezone.now() - timedelta(days=30)
    return User.objects.filter(
        is_active=True,
        last_login__lt=inactive_before,
    ).update(is_active=False)
