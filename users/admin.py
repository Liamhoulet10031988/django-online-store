from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Payment, User

admin.site.register(User, UserAdmin)
admin.site.register(Payment)
