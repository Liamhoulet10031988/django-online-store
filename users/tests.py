from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from stripe import StripeError

from materials.models import Course
from users.models import Payment, User
from users.services import (
    StripeServiceError,
    create_stripe_price,
    create_stripe_product,
    create_stripe_session,
    retrieve_stripe_session,
)


class UserAPITestCase(APITestCase):
    """Проверяет все действия API пользователей."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="api-user",
            email="api-user@example.com",
            password="test-password",
            first_name="Иван",
            last_name="Иванов",
        )
        self.other_user = User.objects.create_user(
            username="other-api-user",
            email="other-api-user@example.com",
            password="test-password",
            last_name="Петров",
        )
        self.list_url = reverse("materials:user-list")
        self.detail_url = reverse(
            "materials:user-detail",
            args=[self.user.pk],
        )

    def test_anonymous_user_can_register(self):
        response = self.client.post(
            self.list_url,
            {
                "username": "new-user",
                "email": "new-user@example.com",
                "password": "test-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(
            User.objects.get(email="new-user@example.com").check_password(
                "test-password"
            )
        )

    def test_authenticated_user_can_list_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_user_can_retrieve_other_profile_with_private_fields_hidden(self):
        self.client.force_authenticate(user=self.user)
        other_detail_url = reverse(
            "materials:user-detail",
            args=[self.other_user.pk],
        )
        response = self.client.get(other_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("last_name"), None)
        self.assertEqual(response.data.get("payments"), None)

    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.detail_url,
            {"city": "Москва"},
            format="json",
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.city, "Москва")

    def test_user_cannot_update_other_profile(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            self.detail_url,
            {"city": "Санкт-Петербург"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_delete_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.filter(pk=self.user.pk).exists(), False)


class PaymentAPITestCase(APITestCase):
    """Проверяет список и фильтрацию платежей."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="payer",
            email="payer@example.com",
            password="test-password",
        )
        self.course = Course.objects.create(
            title="Оплаченный курс",
            owner=self.user,
        )
        Payment.objects.create(
            user=self.user,
            payment_date=timezone.now(),
            paid_course=self.course,
            amount="1500.00",
            payment_method=Payment.PAYMENT_METHOD_TRANSFER,
        )
        self.url = reverse("materials:payment-list")

    def test_authenticated_user_can_get_payments(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_payments_can_be_filtered_by_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self.url,
            {"paid_course": self.course.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_user_cannot_get_payments(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTAPITestCase(APITestCase):
    """Проверяет получение и обновление JWT-токенов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="jwt-user",
            email="jwt@example.com",
            password="test-password",
        )

    def test_user_can_receive_and_refresh_tokens(self):
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "email": self.user.email,
                "password": "test-password",
            },
            format="json",
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in token_response.data)
        self.assertTrue("refresh" in token_response.data)

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in refresh_response.data)


class StripePaymentAPITestCase(APITestCase):
    """Проверяет создание платежа и синхронизацию статуса Stripe."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="stripe-user",
            email="stripe-user@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-stripe-user",
            email="other-stripe-user@example.com",
            password="test-password",
        )
        self.course = Course.objects.create(
            title="Django с оплатой",
            owner=self.user,
        )
        self.create_url = reverse("materials:payment-create")

    @patch("users.views.create_stripe_session")
    @patch("users.views.create_stripe_price")
    @patch("users.views.create_stripe_product")
    def test_authenticated_user_can_create_stripe_payment(
        self,
        product_mock,
        price_mock,
        session_mock,
    ):
        product_mock.return_value = SimpleNamespace(id="prod_test")
        price_mock.return_value = SimpleNamespace(id="price_test")
        session_mock.return_value = SimpleNamespace(
            id="cs_test_session",
            url="https://checkout.stripe.com/c/pay/test",
            status=Payment.SESSION_STATUS_OPEN,
            payment_status=Payment.PAYMENT_STATUS_UNPAID,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            {"paid_course": self.course.pk, "amount": "1500.25"},
            format="json",
        )

        payment = Payment.objects.get()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.paid_course, self.course)
        self.assertEqual(payment.amount, Decimal("1500.25"))
        self.assertEqual(
            payment.payment_method,
            Payment.PAYMENT_METHOD_STRIPE,
        )
        self.assertEqual(payment.stripe_product_id, "prod_test")
        self.assertEqual(payment.stripe_price_id, "price_test")
        self.assertEqual(payment.stripe_session_id, "cs_test_session")
        self.assertEqual(response.data["payment_link"], payment.payment_link)
        product_mock.assert_called_once_with(self.course)
        price_mock.assert_called_once_with("prod_test", Decimal("1500.25"))
        session_mock.assert_called_once_with(
            "price_test",
            "http://127.0.0.1:8000/api/payments/?payment=success",
            "http://127.0.0.1:8000/api/payments/?payment=cancelled",
        )

    def test_anonymous_user_cannot_create_payment(self):
        response = self.client.post(
            self.create_url,
            {"paid_course": self.course.pk, "amount": "1500.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Payment.objects.count(), 0)

    @patch("users.views.create_stripe_product")
    def test_invalid_amount_does_not_call_stripe(self, product_mock):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            {"paid_course": self.course.pk, "amount": "0.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.count(), 0)
        product_mock.assert_not_called()

    @patch("users.views.create_stripe_product")
    def test_stripe_error_returns_502_without_payment(self, product_mock):
        product_mock.side_effect = StripeServiceError("Stripe unavailable")
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            {"paid_course": self.course.pk, "amount": "1500.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(Payment.objects.count(), 0)

    @patch("users.views.retrieve_stripe_session")
    def test_owner_can_sync_payment_status(self, retrieve_mock):
        payment = self.create_payment()
        retrieve_mock.return_value = SimpleNamespace(
            status=Payment.SESSION_STATUS_COMPLETE,
            payment_status=Payment.PAYMENT_STATUS_PAID,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("materials:payment-status", args=[payment.pk])
        )

        payment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            payment.stripe_session_status,
            Payment.SESSION_STATUS_COMPLETE,
        )
        self.assertEqual(payment.payment_status, Payment.PAYMENT_STATUS_PAID)
        retrieve_mock.assert_called_once_with("cs_test_session")

    @patch("users.views.retrieve_stripe_session")
    def test_user_cannot_sync_another_users_payment(self, retrieve_mock):
        payment = self.create_payment()
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            reverse("materials:payment-status", args=[payment.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        retrieve_mock.assert_not_called()

    @patch("users.views.retrieve_stripe_session")
    def test_status_stripe_error_returns_502(self, retrieve_mock):
        payment = self.create_payment()
        retrieve_mock.side_effect = StripeServiceError("Stripe unavailable")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("materials:payment-status", args=[payment.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def create_payment(self):
        return Payment.objects.create(
            user=self.user,
            payment_date=timezone.now(),
            paid_course=self.course,
            amount="1500.00",
            payment_method=Payment.PAYMENT_METHOD_STRIPE,
            stripe_product_id="prod_test",
            stripe_price_id="price_test",
            stripe_session_id="cs_test_session",
            payment_link="https://checkout.stripe.com/c/pay/test",
            stripe_session_status=Payment.SESSION_STATUS_OPEN,
            payment_status=Payment.PAYMENT_STATUS_UNPAID,
        )


@override_settings(
    STRIPE_SECRET_KEY="sk_test_example",
    STRIPE_CURRENCY="rub",
)
class StripeServiceTestCase(APITestCase):
    """Проверяет параметры запросов сервисного слоя Stripe."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="service-user",
            email="service-user@example.com",
            password="test-password",
        )
        self.course = Course.objects.create(
            title="Курс для Stripe",
            owner=self.user,
        )

    @patch("users.services.stripe.Product.create")
    def test_product_contains_course_data(self, product_create_mock):
        product_create_mock.return_value = SimpleNamespace(id="prod_test")

        product = create_stripe_product(self.course)

        self.assertEqual(product.id, "prod_test")
        product_create_mock.assert_called_once_with(
            name=self.course.title,
            metadata={"course_id": str(self.course.pk)},
        )

    @patch("users.services.stripe.Price.create")
    def test_price_uses_integer_kopecks_and_product_id(
        self,
        price_create_mock,
    ):
        price_create_mock.return_value = SimpleNamespace(id="price_test")

        price = create_stripe_price("prod_test", Decimal("1500.25"))

        self.assertEqual(price.id, "price_test")
        price_create_mock.assert_called_once_with(
            currency="rub",
            unit_amount=150025,
            product="prod_test",
        )

    @patch("users.services.stripe.checkout.Session.create")
    def test_session_uses_price_and_redirect_urls(self, session_create_mock):
        session_create_mock.return_value = SimpleNamespace(id="cs_test")

        session = create_stripe_session(
            "price_test",
            "https://example.com/success",
            "https://example.com/cancel",
        )

        self.assertEqual(session.id, "cs_test")
        session_create_mock.assert_called_once_with(
            line_items=[{"price": "price_test", "quantity": 1}],
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

    @patch("users.services.stripe.Product.create")
    def test_stripe_sdk_error_becomes_service_error(
        self,
        product_create_mock,
    ):
        product_create_mock.side_effect = StripeError("Stripe failure")

        with self.assertRaises(StripeServiceError):
            create_stripe_product(self.course)

    @patch("users.services.stripe.checkout.Session.retrieve")
    def test_session_retrieve_uses_saved_session_id(self, retrieve_mock):
        retrieve_mock.return_value = SimpleNamespace(id="cs_test")

        session = retrieve_stripe_session("cs_test")

        self.assertEqual(session.id, "cs_test")
        retrieve_mock.assert_called_once_with("cs_test")

    @override_settings(STRIPE_SECRET_KEY="")
    def test_missing_secret_key_becomes_service_error(self):
        with self.assertRaises(StripeServiceError):
            create_stripe_product(self.course)


class DocumentationAPITestCase(APITestCase):
    """Проверяет доступность OpenAPI, Swagger UI и Redoc."""

    def test_openapi_schema_is_available(self):
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_is_available(self):
        response = self.client.get(reverse("swagger-ui"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_is_available(self):
        response = self.client.get(reverse("redoc"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
