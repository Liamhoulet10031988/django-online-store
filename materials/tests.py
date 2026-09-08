from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course, Lesson, Subscription
from users.models import User


class LessonAPITestCase(APITestCase):
    """Проверяет CRUD уроков, валидатор и права доступа."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="test-password",
        )
        self.moderator = User.objects.create_user(
            username="moderator",
            email="moderator@example.com",
            password="test-password",
        )
        moderators = Group.objects.create(name="Модераторы")
        self.moderator.groups.add(moderators)

        self.course = Course.objects.create(
            title="Python",
            owner=self.owner,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Введение",
            video_url="https://youtube.com/watch?v=123",
            owner=self.owner,
        )

        self.list_url = reverse("materials:lesson-list-create")
        self.detail_url = reverse(
            "materials:lesson-detail",
            args=[self.lesson.pk],
        )

    def test_owner_can_create_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                "course": self.course.pk,
                "title": "Новый урок",
                "video_url": "https://youtube.com/watch?v=456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(
            Lesson.objects.get(title="Новый урок").owner,
            self.owner,
        )

    def test_lesson_rejects_external_link(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                "course": self.course.pk,
                "title": "Чужой ресурс",
                "video_url": "https://example.com/video",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["video_url"][0],
            "Разрешены ссылки только на youtube.com.",
        )

    def test_lesson_rejects_similar_external_domain(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                "course": self.course.pk,
                "title": "Поддельный домен",
                "video_url": "https://youtube.com.example.org/video",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_retrieve_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Введение")

    def test_owner_can_update_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.detail_url,
            {"title": "Обновлённое введение"},
            format="json",
        )

        self.lesson.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.lesson.title, "Обновлённое введение")

    def test_owner_can_delete_lesson(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_anonymous_user_cannot_get_lessons(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_cannot_retrieve_owner_lesson(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_user_cannot_update_owner_lesson(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            self.detail_url,
            {"title": "Чужое изменение"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_user_cannot_delete_owner_lesson(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_moderator_can_retrieve_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_moderator_can_update_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(
            self.detail_url,
            {"title": "Проверено модератором"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_moderator_cannot_create_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(
            self.list_url,
            {"course": self.course.pk, "title": "Запрещено"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_cannot_delete_lesson(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionAPITestCase(APITestCase):
    """Проверяет переключение подписки и поле курса."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="subscriber",
            email="subscriber@example.com",
            password="test-password",
        )
        self.course = Course.objects.create(
            title="Django REST Framework",
            owner=self.user,
        )
        self.subscription_url = reverse("materials:subscription")
        self.course_detail_url = reverse(
            "materials:course-detail",
            args=[self.course.pk],
        )

    def test_user_can_add_subscription(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.subscription_url,
            {"course_id": self.course.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена.")
        self.assertEqual(Subscription.objects.count(), 1)

    def test_second_request_removes_subscription(self):
        Subscription.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.subscription_url,
            {"course_id": self.course.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена.")
        self.assertEqual(Subscription.objects.count(), 0)

    def test_subscription_returns_404_for_unknown_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.subscription_url,
            {"course_id": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_subscription_returns_404_without_course_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.subscription_url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_change_subscription(self):
        response = self.client.post(
            self.subscription_url,
            {"course_id": self.course.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_course_contains_false_subscription_status(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.course_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_subscribed"], False)

    def test_course_contains_true_subscription_status(self):
        Subscription.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.course_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_subscribed"], True)


class PaginationAPITestCase(APITestCase):
    """Проверяет пагинацию списков курсов и уроков."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="test-password",
        )
        self.course = Course.objects.create(
            title="Основной курс",
            owner=self.user,
        )
        for number in range(7):
            Lesson.objects.create(
                course=self.course,
                title=f"Урок {number}",
                owner=self.user,
            )
        for number in range(6):
            Course.objects.create(
                title=f"Курс {number}",
                owner=self.user,
            )
        self.client.force_authenticate(user=self.user)

    def test_lesson_list_is_paginated(self):
        response = self.client.get(
            reverse("materials:lesson-list-create")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 5)

    def test_course_list_is_paginated(self):
        response = self.client.get(reverse("materials:course-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 5)

    def test_client_can_change_page_size(self):
        response = self.client.get(
            reverse("materials:lesson-list-create"),
            {"page_size": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_page_size_cannot_exceed_maximum(self):
        for number in range(18):
            Lesson.objects.create(
                course=self.course,
                title=f"Дополнительный урок {number}",
                owner=self.user,
            )
        response = self.client.get(
            reverse("materials:lesson-list-create"),
            {"page_size": 100},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)


class CourseAPITestCase(APITestCase):
    """Проверяет CRUD курсов и действующие права доступа."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="course-owner",
            email="course-owner@example.com",
            password="test-password",
        )
        self.moderator = User.objects.create_user(
            username="course-moderator",
            email="course-moderator@example.com",
            password="test-password",
        )
        moderators = Group.objects.create(name="Модераторы")
        self.moderator.groups.add(moderators)
        self.course = Course.objects.create(
            title="Курс для CRUD",
            owner=self.owner,
        )
        self.list_url = reverse("materials:course-list")
        self.detail_url = reverse(
            "materials:course-detail",
            args=[self.course.pk],
        )

    def test_owner_can_create_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {"title": "Новый курс"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Course.objects.get(title="Новый курс").owner,
            self.owner,
        )

    def test_owner_can_retrieve_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_can_update_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.detail_url,
            {"title": "Обновлённый курс"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_can_delete_course(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_moderator_can_list_courses(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_moderator_cannot_create_course(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(
            self.list_url,
            {"title": "Запрещённый курс"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_cannot_delete_course(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
