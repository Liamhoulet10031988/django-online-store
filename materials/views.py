from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, Lesson, Subscription
from materials.paginators import MaterialsPagination
from materials.permissions import (
    IsNotModerator,
    IsOwnerOrModerator,
    is_moderator,
)
from materials.serializers import (
    CourseSerializer,
    LessonSerializer,
    SubscriptionRequestSerializer,
    SubscriptionResponseSerializer,
)
from materials.tasks import send_course_update_email


class CourseViewSet(viewsets.ModelViewSet):
    """Выполняет все CRUD-операции для курсов."""

    queryset = Course.objects.all().order_by("pk")
    serializer_class = CourseSerializer
    pagination_class = MaterialsPagination

    def get_queryset(self):
        """Возвращает все курсы модератору и только свои остальным."""
        queryset = Course.objects.all().order_by("pk")
        if is_moderator(self.request.user):
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Подбирает права доступа для текущего действия с курсом."""
        permission_classes = [IsAuthenticated]

        if self.action == "create":
            permission_classes.append(IsNotModerator)
        elif self.action == "destroy":
            permission_classes.extend(
                (IsNotModerator, IsOwnerOrModerator)
            )
        elif self.action in ("retrieve", "update", "partial_update"):
            permission_classes.append(IsOwnerOrModerator)

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Назначает владельцем курса авторизованного пользователя."""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Обновляет курс и ставит в очередь письмо подписчикам."""
        previous_updated_at = serializer.instance.updated_at
        course = serializer.save()

        if timezone.now() - previous_updated_at >= timedelta(hours=4):
            send_course_update_email.delay(course.pk)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Возвращает все уроки или создаёт новый урок."""

    queryset = Lesson.objects.all().order_by("pk")
    serializer_class = LessonSerializer
    pagination_class = MaterialsPagination

    def get_queryset(self):
        """Возвращает все уроки модератору и только свои остальным."""
        queryset = Lesson.objects.all().order_by("pk")
        if is_moderator(self.request.user):
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Запрещает модератору создавать уроки."""
        permission_classes = [IsAuthenticated]
        if self.request.method == "POST":
            permission_classes.append(IsNotModerator)
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Назначает владельцем урока авторизованного пользователя."""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """Возвращает, изменяет или удаляет один урок."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        """Ограничивает обычного пользователя его собственными уроками."""
        queryset = Lesson.objects.all()
        if is_moderator(self.request.user):
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Разрешает изменение владельцу/модератору, удаление — владельцу."""
        permission_classes = [IsAuthenticated, IsOwnerOrModerator]
        if self.request.method == "DELETE":
            permission_classes.append(IsNotModerator)
        return [permission() for permission in permission_classes]


class SubscriptionAPIView(APIView):
    """Добавляет подписку на курс или удаляет существующую."""

    @extend_schema(
        summary="Переключить подписку на курс",
        description=(
            "Создаёт подписку, если её нет, или удаляет существующую."
        ),
        request=SubscriptionRequestSerializer,
        responses={
            200: SubscriptionResponseSerializer,
            400: OpenApiResponse(description="Некорректный ID курса."),
            401: OpenApiResponse(
                description="JWT не передан или недействителен."
            ),
            404: OpenApiResponse(description="Курс не найден."),
        },
        tags=["Подписки"],
    )
    def post(self, request):
        user = request.user
        serializer = SubscriptionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data["course_id"]
        course = get_object_or_404(Course, pk=course_id)
        subscriptions = Subscription.objects.filter(
            user=user,
            course=course,
        )

        if subscriptions.exists():
            subscriptions.delete()
            message = "Подписка удалена."
        else:
            Subscription.objects.create(user=user, course=course)
            message = "Подписка добавлена."

        return Response({"message": message})
