from decimal import Decimal

from rest_framework import serializers

from materials.models import Course
from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Преобразует данные платежа в JSON и обратно."""

    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "payment_link",
            "stripe_session_status",
            "payment_status",
        )
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    """Проверяет курс и сумму для создания оплаты через Stripe."""

    paid_course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all()
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Описывает единый JSON-ответ с сообщением об ошибке."""

    detail = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Преобразует данные профиля в JSON и обратно."""

    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "country",
            "city",
            "avatar",
            "payments",
        )

    def to_representation(self, instance):
        """Скрывает фамилию и платежи при просмотре чужого профиля."""
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user != instance:
            representation.pop("last_name", None)
            representation.pop("payments", None)

        return representation


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Проверяет данные и создаёт пользователя с хешированным паролем."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "phone_number",
            "country",
            "city",
            "avatar",
        )

    def validate_email(self, value):
        """Не допускает повторную регистрацию электронной почты."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Пользователь с такой электронной почтой уже существует."
            )
        return value

    def validate_username(self, value):
        """Не допускает повторную регистрацию имени пользователя."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким именем уже существует."
            )
        return value

    def create(self, validated_data):
        """Создаёт пользователя через create_user для хеширования пароля."""
        return User.objects.create_user(**validated_data)
