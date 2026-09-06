from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course
from users.models import Payment, User


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
