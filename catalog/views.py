from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from catalog.forms import ProductForm
from catalog.models import Contact, Product


class ProductListView(ListView):
    """Показывает список товаров интернет-магазина."""

    model = Product
    template_name = "catalog/home.html"
    context_object_name = "products"
    paginate_by = 6

    def get_queryset(self):
        """Возвращает товары, отсортированные по идентификатору."""
        return super().get_queryset().order_by("pk")


class ProductDetailView(DetailView):
    """Показывает подробную информацию об одном товаре."""

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class ProductCreateView(CreateView):
    """Создаёт новый товар через ProductForm."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"

    def get_success_url(self):
        """Возвращает адрес страницы созданного товара."""
        return reverse(
            "catalog:product_detail",
            kwargs={"pk": self.object.pk},
        )


class ProductUpdateView(UpdateView):
    """Изменяет существующий товар через ProductForm."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"

    def get_success_url(self):
        """Возвращает адрес страницы изменённого товара."""
        return reverse(
            "catalog:product_detail",
            kwargs={"pk": self.object.pk},
        )


class ProductDeleteView(DeleteView):
    """Удаляет товар после подтверждения."""

    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:home")


class ContactsView(View):
    """Показывает контакты и принимает данные формы."""

    def get(self, request):
        """Обрабатывает открытие страницы контактов."""
        contacts_list = Contact.objects.all()
        context = {"contacts": contacts_list}

        return render(request, "catalog/contacts.html", context)

    def post(self, request):
        """Обрабатывает отправку формы обратной связи."""
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        print("Получены данные формы:")
        print(f"Имя: {name}")
        print(f"Телефон: {phone}")
        print(f"Сообщение: {message}")

        return HttpResponse(
            f"Спасибо, {name}! "
            "Ваше сообщение успешно отправлено."
        )
