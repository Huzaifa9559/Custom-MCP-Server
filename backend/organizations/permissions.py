"""
Permission utilities for organization-based access control.

This module provides utility functions for enforcing permission checks
at the GraphQL resolver level. All permission checks must be enforced
here, not in the frontend, ensuring security at the API layer.

All functions raise PermissionError which should be caught and converted
to GraphQLError in GraphQL resolvers.
"""
from typing import Optional
from django.contrib.auth import get_user_model
from organizations.models import OrganizationMembership, Organization


User = get_user_model()


class PermissionError(Exception):
    """
    Custom exception for permission-related errors.
    
    This exception is raised when a permission check fails. It should be
    caught in GraphQL resolvers and converted to GraphQLError with proper
    error messages for the client.
    
    Attributes:
        message: Error message describing the permission failure
    """
    
    def __init__(self, message: str):
        """
        Initialize PermissionError with a message.
        
        Args:
            message: Error message describing the permission failure
        """
        self.message = message
        super().__init__(self.message)


def get_user_active_organization(user: User) -> Organization:
    """
    Get the user's currently active organization.
    
    This function retrieves the organization that the user has selected
    as their active organization for the current session.
    
    Args:
        user: User instance
        
    Returns:
        Organization: The user's active organization
        
    Raises:
        PermissionError: If user has no active organization set or is not a member
    """
    if not user.active_organization_id:
        raise PermissionError(
            'No active organization selected. Please select an organization first.'
        )
    
    try:
        membership = OrganizationMembership.objects.select_related('organization').get(
            user=user,
            organization_id=user.active_organization_id
        )
        return membership.organization
    except OrganizationMembership.DoesNotExist:
        raise PermissionError(
            f'User is not a member of organization {user.active_organization_id}.'
        )


def check_user_in_organization(user: User, organization_id: int) -> bool:
    """
    Check if a user is a member of a specific organization.
    
    This is a non-raising check function useful for conditional logic.
    For permission enforcement, use require_organization_member instead.
    
    Args:
        user: User instance
        organization_id: ID of the organization to check
        
    Returns:
        bool: True if user is a member, False otherwise
    """
    return OrganizationMembership.objects.filter(
        user=user,
        organization_id=organization_id
    ).exists()


def get_user_role_in_organization(user: User, organization_id: int) -> Optional[str]:
    """
    Get the user's role in a specific organization.
    
    Args:
        user: User instance
        organization_id: ID of the organization
        
    Returns:
        str: User's role (ADMIN or MEMBER) or None if not a member
    """
    try:
        membership = OrganizationMembership.objects.get(
            user=user,
            organization_id=organization_id
        )
        return membership.role
    except OrganizationMembership.DoesNotExist:
        return None


def require_organization_member(user: User, organization_id: int) -> None:
    """
    Require that a user is a member of a specific organization.
    
    This function raises PermissionError if the user is not a member,
    ensuring that only organization members can access organization resources.
    
    Args:
        user: User instance
        organization_id: ID of the organization
        
    Raises:
        PermissionError: If user is not a member of the organization
    """
    if not check_user_in_organization(user, organization_id):
        # Try to get organization name for better error message
        try:
            org = Organization.objects.get(id=organization_id)
            org_name = org.name
        except Organization.DoesNotExist:
            org_name = f'Organization {organization_id}'
        
        raise PermissionError(
            f'User is not a member of organization "{org_name}". '
            'Access denied.'
        )


def require_organization_admin(user: User, organization_id: int) -> None:
    """
    Require that a user is an ADMIN of a specific organization.
    
    This function enforces that only administrators can perform
    administrative actions like creating documents or inviting users.
    
    Args:
        user: User instance
        organization_id: ID of the organization
        
    Raises:
        PermissionError: If user is not an admin of the organization
    """
    role = get_user_role_in_organization(user, organization_id)
    
    if role != OrganizationMembership.Role.ADMIN:
        # Try to get organization name for better error message
        try:
            org = Organization.objects.get(id=organization_id)
            org_name = org.name
        except Organization.DoesNotExist:
            org_name = f'Organization {organization_id}'
        
        if role is None:
            raise PermissionError(
                f'User is not a member of organization "{org_name}". '
                'Only administrators can perform this action.'
            )
        else:
            raise PermissionError(
                f'User must be an ADMIN in organization "{org_name}" to perform this action. '
                f'Current role: {role}.'
            )


def require_active_organization(user: User) -> int:
    """
    Require that a user has an active organization selected.
    
    This function ensures that operations that require organization context
    can only be performed when a user has selected an active organization.
    
    Args:
        user: User instance
        
    Returns:
        int: The active organization ID
        
    Raises:
        PermissionError: If user has no active organization selected
    """
    if not user.active_organization_id:
        raise PermissionError(
            'No active organization selected. Please select an organization to continue.'
        )
    
    # Verify user is still a member of the active organization
    require_organization_member(user, user.active_organization_id)
    
    return user.active_organization_id


def can_user_access_document(user: User, document_organization_id: int) -> bool:
    """
    Check if a user can access a document based on organization membership.
    
    This is a convenience function for checking document access permissions.
    
    Args:
        user: User instance
        document_organization_id: Organization ID of the document
        
    Returns:
        bool: True if user can access the document, False otherwise
    """
    return check_user_in_organization(user, document_organization_id)


def require_document_access(user: User, document_organization_id: int) -> None:
    """
    Require that a user can access a document.
    
    This function enforces document access permissions based on
    organization membership. Both ADMIN and MEMBER roles can access documents.
    
    Args:
        user: User instance
        document_organization_id: Organization ID of the document
        
    Raises:
        PermissionError: If user cannot access the document
    """
    require_organization_member(user, document_organization_id)

