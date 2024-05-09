from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Follow

Member = get_user_model()


@admin.register(Follow)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'subscribe_date')
    search_fields = ('user__username', 'author__username')
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


@admin.register(Member)
class MemberAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'password', 'is_superuser', 'is_active', 'date_joined', 'is_staff'
    )
    list_editable = (
        'username', 'email', 'first_name', 'last_name',
        'password', 'is_superuser', 'is_active', 'is_staff'
    )
    list_filter = (
        'email', 'first_name', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name')
    empty_value_display = settings.EMPTY_VALUE_ADMIN_PANEL


admin.site.unregister(Group)
