from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, UpdateView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.forms import UserProfileForm, UserRegisterForm
from users.models import Payment, User
from users.permissions import IsCurrentUser
from users.serializers import (
    ErrorResponseSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from users.services import (
    StripeServiceError,
    create_stripe_price,
    create_stripe_product,
    create_stripe_session,
    retrieve_stripe_session,
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

    @extend_schema(
        summary="Получить список платежей",
        description="Возвращает платежи с фильтрацией и сортировкой.",
        parameters=[
            OpenApiParameter(
                name="paid_course",
                type=int,
                description="ID оплаченного курса.",
            ),
            OpenApiParameter(
                name="paid_lesson",
                type=int,
                description="ID оплаченного урока.",
            ),
            OpenApiParameter(
                name="payment_method",
                type=str,
                description="Способ оплаты: cash, transfer или stripe.",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                description="Сортировка: payment_date или -payment_date.",
            ),
        ],
        responses={
            200: PaymentSerializer(many=True),
            401: OpenApiResponse(
                description="JWT не передан или недействителен."
            ),
        },
        tags=["Платежи"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentCreateAPIView(APIView):
    """Создаёт оплату курса и возвращает ссылку Stripe Checkout."""

    @extend_schema(
        summary="Создать оплату курса",
        description=(
            "Создаёт Product, Price и Checkout Session в Stripe, затем "
            "сохраняет платёж текущего пользователя."
        ),
        request=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(
                description=(
                    "Ошибки проверки полей paid_course и amount."
                ),
            ),
            401: OpenApiResponse(
                description="JWT не передан или недействителен."
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ошибка или отсутствие настройки Stripe.",
            ),
        },
        tags=["Платежи"],
    )
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = serializer.validated_data["paid_course"]
        amount = serializer.validated_data["amount"]

        try:
            product = create_stripe_product(course)
            price = create_stripe_price(product.id, amount)
            session = create_stripe_session(
                price.id,
                settings.STRIPE_SUCCESS_URL,
                settings.STRIPE_CANCEL_URL,
            )
        except StripeServiceError:
            return Response(
                {"detail": "Не удалось создать платёж через Stripe."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment = Payment.objects.create(
            user=request.user,
            payment_date=timezone.now(),
            paid_course=course,
            amount=amount,
            payment_method=Payment.PAYMENT_METHOD_STRIPE,
            stripe_product_id=product.id,
            stripe_price_id=price.id,
            stripe_session_id=session.id,
            payment_link=session.url,
            stripe_session_status=session.status,
            payment_status=session.payment_status,
        )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentStatusAPIView(APIView):
    """Получает актуальные статусы Stripe и обновляет локальный платёж."""

    @extend_schema(
        summary="Проверить статус оплаты",
        description=(
            "Получает Checkout Session из Stripe и синхронизирует статусы "
            "с платежом текущего пользователя."
        ),
        responses={
            200: PaymentSerializer,
            401: OpenApiResponse(
                description="JWT не передан или недействителен."
            ),
            404: OpenApiResponse(
                description="Платёж текущего пользователя не найден."
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ошибка или отсутствие настройки Stripe.",
            ),
        },
        tags=["Платежи"],
    )
    def get(self, request, pk):
        payment = get_object_or_404(
            Payment,
            pk=pk,
            user=request.user,
        )

        try:
            session = retrieve_stripe_session(payment.stripe_session_id)
        except StripeServiceError:
            return Response(
                {"detail": "Не удалось проверить платёж через Stripe."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.stripe_session_status = session.status
        payment.payment_status = session.payment_status
        payment.save(
            update_fields=("stripe_session_status", "payment_status")
        )

        return Response(PaymentSerializer(payment).data)
