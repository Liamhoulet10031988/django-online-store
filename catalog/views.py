from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    """Возвращает главную страницу интернет-магазина."""
    return render(request, "catalog/home.html")


def contacts(request):
    """Показывает контакты и принимает данные формы."""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        print("Получены данные формы:")
        print(f"Имя: {name}")
        print(f"Почта: {email}")
        print(f"Сообщение: {message}")

        return HttpResponse(
            f"Спасибо, {name}! Ваше сообщение успешно отправлено."
        )

    return render(request, "catalog/contacts.html")
