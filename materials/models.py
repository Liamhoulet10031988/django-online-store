from django.conf import settings
from django.db import models


class Course(models.Model):
    """Курс, который объединяет учебные уроки."""

    title = models.CharField(max_length=200, verbose_name="Название")
    preview = models.ImageField(
        upload_to="materials/course_previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owned_courses",
        verbose_name="Владелец",
    )

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Урок, который относится к одному курсу."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс",
    )
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    preview = models.ImageField(
        upload_to="materials/lesson_previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    video_url = models.URLField(blank=True, verbose_name="Ссылка на видео")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owned_lessons",
        verbose_name="Владелец",
    )

    def __str__(self):
        return self.title


class Subscription(models.Model):
    """Подписка пользователя на обновления курса."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Курс",
    )

    class Meta:
        unique_together = ("user", "course")
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} — {self.course}"
