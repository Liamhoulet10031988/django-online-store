from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.forms import UserProfileForm, UserRegisterForm
from users.models import Payment, User
from users.permissions import IsCurrentUser
from users.serializers import (
    PaymentSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class RegisterView(FormView):
    """Регистрирует пользователя и отправляет приветственное письмо."""

    template_name = "users/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("catalog:home")

    def form_valid(self, form):
        """Сохраняет пользователя после успешной проверки формы."""
        user = form.save()
        login(self.request, user)
        self.send_welcome_email(user.email)
        return super().form_valid(form)

    def send_welcome_email(self, user_email):
        """Отправляет приветственное письмо новому пользователю."""
        send_mail(
            "Добро пожаловать в Skystore",
            "Спасибо за регистрацию в нашем интернет-магазине!",
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Изменяет профиль текущего пользователя."""

    model = User
    form_class = UserProfileForm
    template_name = "users/profile_form.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        """Возвращает пользователя текущего HTTP-запроса."""
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """Выполняет CRUD пользователей и регистрацию через API."""

    queryset = User.objects.all()

    def get_serializer_class(self):
        """Использует отдельный сериализатор для регистрации."""
        if self.action == "create":
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        """Открывает регистрацию и защищает изменение чужого профиля."""
        if self.action == "create":
            permission_classes = [AllowAny]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsAuthenticated, IsCurrentUser]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


class PaymentListAPIView(generics.ListAPIView):
    """Возвращает платежи с фильтрацией и сортировкой по дате."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ("paid_course", "paid_lesson", "payment_method")
    ordering_fields = ("payment_date",)
