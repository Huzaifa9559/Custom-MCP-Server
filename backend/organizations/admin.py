"""
Django admin configuration for organizations app.

This module registers Organization and OrganizationMembership models
with Django admin and customizes the admin interface.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for Organization model.
    
    Provides a comprehensive admin interface for managing organizations,
    including viewing membership statistics.
    """
    
    list_display = ('name', 'member_count_display', 'admin_count_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'member_count_display', 'admin_count_display')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name',)
        }),
        (_('Statistics'), {
            'fields': ('member_count_display', 'admin_count_display'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def member_count_display(self, obj: Organization) -> str:
        """
        Display member count with color coding.
        
        Args:
            obj: Organization instance
            
        Returns:
            str: Formatted member count
        """
        count = obj.member_count
        color = 'green' if count > 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    member_count_display.short_description = _('Members')
    member_count_display.admin_order_field = 'memberships__count'
    
    def admin_count_display(self, obj: Organization) -> str:
        """
        Display admin count.
        
        Args:
            obj: Organization instance
            
        Returns:
            str: Formatted admin count
        """
        return obj.admin_count
    admin_count_display.short_description = _('Admins')


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """
    Admin interface for OrganizationMembership model.
    
    Provides admin interface for managing user memberships in organizations,
    including role assignment and membership history.
    """
    
    list_display = ('user', 'organization', 'role_display', 'joined_at')
    list_filter = ('role', 'joined_at', 'organization')
    search_fields = ('user__email', 'organization__name')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)
    
    fieldsets = (
        (_('Membership Information'), {
            'fields': ('user', 'organization', 'role')
        }),
        (_('Timestamps'), {
            'fields': ('joined_at',),
            'classes': ('collapse',),
        }),
    )
    
    def role_display(self, obj: OrganizationMembership) -> str:
        """
        Display role with color coding.
        
        Args:
            obj: OrganizationMembership instance
            
        Returns:
            str: Formatted role display
        """
        color = 'red' if obj.is_admin else 'blue'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_display.short_description = _('Role')
    role_display.admin_order_field = 'role'
    
    def get_queryset(self, request):
        """
        Optimize queryset by selecting related objects.
        
        Args:
            request: HTTP request object
            
        Returns:
            QuerySet: Optimized queryset
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'organization')
