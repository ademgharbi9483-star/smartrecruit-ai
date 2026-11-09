"""
SmartRecruit AI — Admin Authentification
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter   = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['-date_joined']

    fieldsets = (
        (None,              {'fields': ('email', 'password')}),
        ('Informations',    {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Rôle & Droits',   {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',           {'fields': ('date_joined', 'last_login')}),
        ('Reset Password',  {'fields': ('reset_token', 'reset_token_expires')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    readonly_fields = ['date_joined', 'last_login']
