"""
User models.

This module contains the custom User model that extends Django's AbstractUser
to use email as the primary authentication identifier instead of username.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    
    This manager provides helper methods for creating users and superusers.
    """
    
    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields
    ) -> 'User':
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: User's email address (required, must be unique)
            password: User's password
            **extra_fields: Additional fields for the user model
            
        Returns:
            User: The created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        # Normalize email address (lowercase)
        email = self.normalize_email(email)
        
        # Create user instance
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields
    ) -> 'User':
        """
        Create and save a superuser with the given email and password.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional fields for the user model
            
        Returns:
            User: The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email as the unique identifier.
    
    This model extends Django's AbstractUser and changes the authentication
    mechanism to use email instead of username. Users can belong to multiple
    organizations, with one active organization at a time for multi-tenant
    context switching.
    
    Attributes:
        email: User's email address (unique, used for authentication)
        username: Not used for authentication (kept for compatibility)
        active_organization_id: ID of the currently selected organization
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
    """
    
    # Email is the primary authentication field
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. User email address used for authentication.'),
    )
    
    # Username is not required but kept for compatibility
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,
        null=True,
        help_text=_('Optional. Username (not used for authentication).'),
    )
    
    # Multi-tenant: Track active organization
    active_organization_id = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the currently active organization for this user.'),
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email and password are required, username is optional
    
    # Use custom manager
    objects = UserManager()
    
    class Meta:
        """Meta options for the User model."""
        db_table = 'users_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['active_organization_id']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the user."""
        return self.email
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation of the user."""
        return f'<User: {self.email}>'
    
    @property
    def has_active_organization(self) -> bool:
        """
        Check if user has an active organization set.
        
        Returns:
            bool: True if active_organization_id is set, False otherwise
        """
        return self.active_organization_id is not None
