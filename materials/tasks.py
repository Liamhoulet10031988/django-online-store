from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from materials.models import Course


@shared_task
def send_course_update_email(course_id):
    """Отправляет подписчикам письмо об обновлении курса."""
    course = Course.objects.get(pk=course_id)
    recipient_list = list(
        course.subscriptions.exclude(user__email="").values_list(
            "user__email",
            flat=True,
        )
    )

    if not recipient_list:
        return 0

    return send_mail(
        subject=f"Обновление курса «{course.title}»",
        message=(
            f"В курсе «{course.title}» появились обновления. "
            "Откройте платформу, чтобы посмотреть изменения."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
    )
