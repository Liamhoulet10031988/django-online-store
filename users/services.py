from decimal import Decimal

import stripe
from django.conf import settings
from stripe import StripeError


class StripeServiceError(Exception):
    """Безопасная ошибка взаимодействия приложения со Stripe."""


def configure_stripe():
    """Устанавливает секретный ключ или сообщает об отсутствии настройки."""
    if not settings.STRIPE_SECRET_KEY:
        raise StripeServiceError("Секретный ключ Stripe не настроен.")
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(course):
    """Создаёт Stripe Product для выбранного курса."""
    configure_stripe()
    try:
        return stripe.Product.create(
            name=course.title,
            metadata={"course_id": str(course.pk)},
        )
    except StripeError as error:
        raise StripeServiceError(
            "Не удалось создать продукт Stripe."
        ) from error


def create_stripe_price(product_id, amount: Decimal):
    """Создаёт разовую цену в рублях и передаёт сумму в копейках."""
    configure_stripe()
    amount_in_kopecks = int(amount * 100)
    try:
        return stripe.Price.create(
            currency=settings.STRIPE_CURRENCY,
            unit_amount=amount_in_kopecks,
            product=product_id,
        )
    except StripeError as error:
        raise StripeServiceError(
            "Не удалось создать цену Stripe."
        ) from error


def create_stripe_session(price_id, success_url, cancel_url):
    """Создаёт Checkout Session и возвращает платёжную ссылку."""
    configure_stripe()
    try:
        return stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except StripeError as error:
        raise StripeServiceError(
            "Не удалось создать сессию Stripe."
        ) from error


def retrieve_stripe_session(session_id):
    """Получает из Stripe актуальные данные Checkout Session."""
    configure_stripe()
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except StripeError as error:
        raise StripeServiceError(
            "Не удалось получить сессию Stripe."
        ) from error
