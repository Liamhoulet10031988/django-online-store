from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from common.forms import FormStyleMixin
from users.models import User


class UserRegisterForm(FormStyleMixin, UserCreationForm):
    """Форма регистрации пользователя."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "username",
            "password1",
            "password2",
        )


class UserLoginForm(FormStyleMixin, AuthenticationForm):
    """Форма входа пользователя."""


class UserProfileForm(FormStyleMixin, forms.ModelForm):
    """Форма изменения профиля пользователя."""

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "avatar",
            "phone_number",
            "city",
            "country",
        )
