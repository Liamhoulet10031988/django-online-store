from rest_framework.permissions import BasePermission

MODERATOR_GROUP_NAME = "Модераторы"


def is_moderator(user):
    """Проверяет, входит ли пользователь в группу модераторов."""
    return user.groups.filter(name=MODERATOR_GROUP_NAME).exists()


class IsNotModerator(BasePermission):
    """Запрещает действие пользователям из группы модераторов."""

    def has_permission(self, request, view):
        return not is_moderator(request.user)


class IsOwnerOrModerator(BasePermission):
    """Разрешает действие владельцу объекта или модератору."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or is_moderator(request.user)
