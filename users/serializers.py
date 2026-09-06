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
