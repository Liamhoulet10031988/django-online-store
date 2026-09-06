from rest_framework.permissions import BasePermission


class IsCurrentUser(BasePermission):
    """Разрешает изменение и удаление только собственного профиля."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user
