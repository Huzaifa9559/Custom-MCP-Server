"""
Organization models.

This module contains models for multi-tenant organization management,
including organization membership with role-based access control (RBAC).
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


User = get_user_model()


class Organization(models.Model):
    """
    Organization model for multi-tenant architecture.
    
    Organizations serve as containers for documents and users. Each user can
    belong to multiple organizations, with different roles in each. This enables
    multi-tenant functionality where data is isolated per organization.
    
    Attributes:
        name: Organization name (required, unique)
        created_at: Timestamp when the organization was created
        updated_at: Timestamp when the organization was last updated
    """
    
    name = models.CharField(
        _('name'),
        max_length=255,
        unique=True,
        help_text=_('Organization name. Must be unique.'),
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('Timestamp when the organization was created.'),
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('Timestamp when the organization was last updated.'),
    )
    
    class Meta:
        """Meta options for the Organization model."""
        db_table = 'organizations_organization'
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the organization."""
        return self.name
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation of the organization."""
        return f'<Organization: {self.name}>'
    
    @property
    def member_count(self) -> int:
        """
        Get the number of members in this organization.
        
        Returns:
            int: Number of members
        """
        return self.memberships.count()
    
    @property
    def admin_count(self) -> int:
        """
        Get the number of administrators in this organization.
        
        Returns:
            int: Number of administrators
        """
        return self.memberships.filter(role=OrganizationMembership.Role.ADMIN).count()


class OrganizationMembership(models.Model):
    """
    Membership model linking users to organizations with roles.
    
    This model implements the many-to-many relationship between users and
    organizations, with role information. Each user can have different roles
    in different organizations, enabling flexible access control.
    
    Roles:
        ADMIN: Full access - can create/manage documents, invite users
        MEMBER: Read access - can read documents and ask AI questions
    
    Attributes:
        user: Foreign key to User model
        organization: Foreign key to Organization model
        role: User's role in the organization (ADMIN or MEMBER)
        joined_at: Timestamp when the user joined the organization
    """
    
    class Role(models.TextChoices):
        """
        Role choices for organization membership.
        
        ADMIN: Organization administrator with full permissions
        MEMBER: Organization member with read permissions
        """
        ADMIN = 'ADMIN', _('Admin')
        MEMBER = 'MEMBER', _('Member')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        help_text=_('User who is a member of this organization.'),
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text=_('Organization this user belongs to.'),
    )
    role = models.CharField(
        _('role'),
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text=_('User\'s role in the organization.'),
    )
    joined_at = models.DateTimeField(
        _('joined at'),
        auto_now_add=True,
        help_text=_('Timestamp when the user joined the organization.'),
    )
    
    class Meta:
        """Meta options for the OrganizationMembership model."""
        db_table = 'organizations_membership'
        verbose_name = _('organization membership')
        verbose_name_plural = _('organization memberships')
        ordering = ['-joined_at']
        # Ensure a user can only have one membership per organization
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['role']),
            models.Index(fields=['joined_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'organization'],
                name='unique_user_organization_membership',
            ),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the membership."""
        return f'{self.user.email} - {self.organization.name} ({self.get_role_display()})'
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation of the membership."""
        return f'<OrganizationMembership: {self.user.email}@{self.organization.name}({self.role})>'
    
    def clean(self) -> None:
        """
        Validate the membership instance.
        
        Raises:
            ValidationError: If validation fails
        """
        if self.role not in [choice[0] for choice in self.Role.choices]:
            raise ValidationError(_('Invalid role selected.'))
    
    def save(self, *args, **kwargs) -> None:
        """
        Save the membership instance after validation.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self) -> bool:
        """
        Check if the user is an administrator.
        
        Returns:
            bool: True if role is ADMIN, False otherwise
        """
        return self.role == self.Role.ADMIN
    
    @property
    def is_member(self) -> bool:
        """
        Check if the user is a member (non-admin).
        
        Returns:
            bool: True if role is MEMBER, False otherwise
        """
        return self.role == self.Role.MEMBER
