from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Преобразует данные профиля в JSON и обратно."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "city",
            "avatar",
        )
