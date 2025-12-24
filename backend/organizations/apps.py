"""
Organizations app configuration.

This app handles multi-tenant organization management and
role-based access control (ADMIN/MEMBER roles).
"""
from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    """Configuration for the organizations application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
    verbose_name = 'Organizations'

