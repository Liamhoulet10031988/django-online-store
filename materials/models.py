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

    def __str__(self):
        return self.title
