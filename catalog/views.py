from django.http import HttpResponse
from django.shortcuts import render

from catalog.models import Contact, Product


def home(request):
    """Возвращает главную страницу интернет-магазина."""
    products = Product.objects.order_by("-created_at", "-id")[:5]

    for product in products:
        print(product)

    return render(
        request,
        "catalog/home.html",
        {"products": products},
    )


def contacts(request):
    """Показывает контакты и принимает данные формы."""
    contacts_list = Contact.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        print("Получены данные формы:")
        print(f"Имя: {name}")
        print(f"Телефон: {phone}")
        print(f"Сообщение: {message}")

        return HttpResponse(
            f"Спасибо, {name}! Ваше сообщение успешно отправлено."
        )

    return render(
        request,
        "catalog/contacts.html",
        {"contacts": contacts_list},
    )
