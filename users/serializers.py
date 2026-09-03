from rest_framework import serializers

from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Преобразует данные платежа в JSON и обратно."""

    class Meta:
        model = Payment
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    """Преобразует данные профиля в JSON и обратно."""

    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "city",
            "avatar",
            "payments",
        )
