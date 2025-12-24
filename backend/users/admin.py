"""
Django admin configuration for users app.

This module registers the User model with Django admin and customizes
the admin interface for user management.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    
    Customizes the Django admin interface to work with email-based
    authentication instead of username.
    """
    
    # Fields to display in the list view
    list_display = ('email', 'is_active', 'is_staff', 'is_superuser', 'active_organization_id', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    # Fieldsets for the detail/edit view
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Organization'), {'fields': ('active_organization_id',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    # Fields that are read-only
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')


