"""
Users app configuration.

This app handles user authentication and user management.
It provides a custom User model with email-based authentication.
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration for the users application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Users'

