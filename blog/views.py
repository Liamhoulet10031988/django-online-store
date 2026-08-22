from django.conf import settings
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from blog.models import Blog


class BlogListView(ListView):
    """Показывает список опубликованных статей."""

    model = Blog
    template_name = "blog/blog_list.html"
    context_object_name = "blogs"

    def get_queryset(self):
        """Возвращает только опубликованные статьи."""
        return super().get_queryset().filter(is_published=True)


class BlogDetailView(DetailView):
    """Показывает статью и увеличивает счетчик просмотров."""

    model = Blog
    template_name = "blog/blog_detail.html"
    context_object_name = "blog"

    def get_object(self, queryset=None):
        """Обновляет просмотры и отправляет письмо на сотом."""
        blog = super().get_object(queryset)
        blog.views_count += 1
        blog.save()

        if blog.views_count == 100:
            send_mail(
                subject="Статья набрала 100 просмотров",
                message=(
                    f"Статья «{blog.title}» набрала 100 просмотров."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )

        return blog


class BlogCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """Создаёт новую статью при наличии права доступа."""

    permission_required = "blog.add_blog"
    model = Blog
    fields = (
        "title",
        "content",
        "preview",
        "is_published",
    )
    template_name = "blog/blog_form.html"
    success_url = reverse_lazy("blog:blog_list")


class BlogUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Изменяет статью при наличии права доступа."""

    permission_required = "blog.change_blog"
    model = Blog
    fields = (
        "title",
        "content",
        "preview",
        "is_published",
    )
    template_name = "blog/blog_form.html"

    def get_success_url(self):
        """Возвращает адрес измененной статьи."""
        return reverse(
            "blog:blog_detail",
            kwargs={"pk": self.object.pk},
        )


class BlogDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView,
):
    """Удаляет статью при наличии права доступа."""

    permission_required = "blog.delete_blog"
    model = Blog
    template_name = "blog/blog_confirm_delete.html"
    success_url = reverse_lazy("blog:blog_list")
