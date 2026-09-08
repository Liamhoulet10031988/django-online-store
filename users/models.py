from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь интернет-магазина."""

    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта"
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Номер телефона",
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Страна",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Город",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        """Возвращает электронную почту пользователя."""
        return self.email


class Payment(models.Model):
    """Платеж пользователя за курс или отдельный урок."""

    PAYMENT_METHOD_CASH = "cash"
    PAYMENT_METHOD_TRANSFER = "transfer"
    PAYMENT_METHOD_STRIPE = "stripe"

    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_METHOD_CASH, "Наличные"),
        (PAYMENT_METHOD_TRANSFER, "Перевод на счет"),
        (PAYMENT_METHOD_STRIPE, "Stripe"),
    )

    SESSION_STATUS_OPEN = "open"
    SESSION_STATUS_COMPLETE = "complete"
    SESSION_STATUS_EXPIRED = "expired"

    SESSION_STATUS_CHOICES = (
        (SESSION_STATUS_OPEN, "Открыта"),
        (SESSION_STATUS_COMPLETE, "Завершена"),
        (SESSION_STATUS_EXPIRED, "Истекла"),
    )

    PAYMENT_STATUS_UNPAID = "unpaid"
    PAYMENT_STATUS_PAID = "paid"
    PAYMENT_STATUS_NO_PAYMENT_REQUIRED = "no_payment_required"

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_UNPAID, "Не оплачено"),
        (PAYMENT_STATUS_PAID, "Оплачено"),
        (PAYMENT_STATUS_NO_PAYMENT_REQUIRED, "Оплата не требуется"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Пользователь",
    )
    payment_date = models.DateTimeField(verbose_name="Дата оплаты")
    paid_course = models.ForeignKey(
        "materials.Course",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="Оплаченный курс",
    )
    paid_lesson = models.ForeignKey(
        "materials.Lesson",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="Оплаченный урок",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Способ оплаты",
    )
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID продукта Stripe",
    )
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID цены Stripe",
    )
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID сессии Stripe",
    )
    payment_link = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Ссылка на оплату",
    )
    stripe_session_status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        blank=True,
        verbose_name="Статус сессии Stripe",
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_UNPAID,
        verbose_name="Статус оплаты",
    )

    def __str__(self):
        """Возвращает краткое описание платежа."""
        return f"{self.user}: {self.amount}"
