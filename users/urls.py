from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from users.forms import UserLoginForm
from users.views import ProfileUpdateView, RegisterView

app_name = "users"

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html",
            authentication_form=UserLoginForm,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "profile/",
        ProfileUpdateView.as_view(),
        name="profile",
    ),
]
