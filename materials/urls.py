from django.urls import include, path
from rest_framework.routers import DefaultRouter

from materials.views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
    SubscriptionAPIView,
)
from users.views import (
    PaymentCreateAPIView,
    PaymentListAPIView,
    PaymentStatusAPIView,
    UserViewSet,
)

app_name = "materials"

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "lessons/",
        LessonListCreateAPIView.as_view(),
        name="lesson-list-create",
    ),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyAPIView.as_view(),
        name="lesson-detail",
    ),
    path(
        "payments/",
        PaymentListAPIView.as_view(),
        name="payment-list",
    ),
    path(
        "payments/create/",
        PaymentCreateAPIView.as_view(),
        name="payment-create",
    ),
    path(
        "payments/<int:pk>/status/",
        PaymentStatusAPIView.as_view(),
        name="payment-status",
    ),
    path(
        "subscriptions/",
        SubscriptionAPIView.as_view(),
        name="subscription",
    ),
]
