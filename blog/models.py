from django.db import models


class Blog(models.Model):
    """Статья учебного блога интернет-магазина."""

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
    )
    content = models.TextField(verbose_name="Содержимое")
    preview = models.ImageField(
        upload_to="blog/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано",
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество просмотров",
    )

    def __str__(self) -> str:
        """Возвращает заголовок статьи."""
        return self.title

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
