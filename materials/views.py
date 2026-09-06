from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from materials.models import Course, Lesson
from materials.permissions import (
    IsNotModerator,
    IsOwnerOrModerator,
    is_moderator,
)
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """Выполняет все CRUD-операции для курсов."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        """Возвращает все курсы модератору и только свои остальным."""
        queryset = Course.objects.all()
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


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Возвращает все уроки или создаёт новый урок."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        """Возвращает все уроки модератору и только свои остальным."""
        queryset = Lesson.objects.all()
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
