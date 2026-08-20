from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render

from catalog.models import Category, Contact, Product


def home(request):
    """Возвращает главную страницу с товарами."""
    products = Product.objects.all()
    products = products.order_by("pk")
    paginator = Paginator(products, 6)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)
    context = {
        "products": products_page,
        "page_obj": products_page,
    }

    return render(request, "catalog/home.html", context)


def product_detail(request, pk):
    """Возвращает страницу с подробной информацией о товаре."""
    product = Product.objects.get(pk=pk)
    context = {"product": product}

    return render(request, "catalog/product_detail.html", context)


def product_create(request):
    """Показывает форму и сохраняет новый товар."""
    categories = Category.objects.all()
    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        category_id = request.POST.get("category", "").strip()
        image = request.FILES.get("image")

        if (
            name == ""
            or description == ""
            or price == ""
            or category_id == ""
            or image is None
        ):
            error = "Заполните все поля формы."
        else:
            try:
                price_number = int(price)
                category = Category.objects.get(pk=category_id)
            except (ValueError, Category.DoesNotExist):
                error = "Проверьте цену и выбранную категорию."
            else:
                if price_number <= 0:
                    error = "Цена должна быть больше нуля."
                else:
                    product = Product.objects.create(
                        name=name,
                        description=description,
                        image=image,
                        category=category,
                        price=price_number,
                    )
                    return redirect(
                        "catalog:product_detail",
                        pk=product.pk,
                    )

    context = {
        "categories": categories,
        "error": error,
    }
    return render(request, "catalog/product_form.html", context)


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

    context = {"contacts": contacts_list}

    return render(request, "catalog/contacts.html", context)
