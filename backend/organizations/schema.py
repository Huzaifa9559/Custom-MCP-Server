"""
GraphQL schema for organizations app.

This module provides GraphQL queries and mutations for organization management,
including listing organizations, setting active organization, and inviting users.
All permission checks are enforced at the resolver level.
"""
import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from organizations.permissions import (
    check_user_in_organization,
    require_organization_admin,
    PermissionError
)


User = get_user_model()


class OrganizationType(DjangoObjectType):
    """
    GraphQL type for Organization model.
    
    Exposes organization fields to the GraphQL API.
    """
    
    class Meta:
        model = Organization
        fields = ('id', 'name', 'created_at', 'updated_at')
        description = 'Organization type representing a multi-tenant organization.'


class OrganizationMembershipType(DjangoObjectType):
    """
    GraphQL type for OrganizationMembership model.
    
    Exposes membership information including user, organization, and role.
    """
    
    role = graphene.String(description='User role in the organization (ADMIN or MEMBER).')
    
    class Meta:
        model = OrganizationMembership
        fields = ('id', 'user', 'organization', 'role', 'joined_at')
        description = 'Organization membership type representing user-organization relationship with role.'


class Query(graphene.ObjectType):
    """
    Root Query type for organizations.
    
    Provides queries for fetching organization data.
    """
    
    organizations = graphene.List(
        OrganizationType,
        required=True,
        description='Get all organizations the authenticated user belongs to.'
    )
    
    def resolve_organizations(self, info) -> list[Organization]:
        """
        Resolve organizations query.
        
        Returns all organizations where the authenticated user is a member.
        Only authenticated users can access this query.
        
        Args:
            info: GraphQL resolver info object
            
        Returns:
            list[Organization]: List of organizations the user belongs to
            
        Raises:
            GraphQLError: If user is not authenticated
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Get all organizations where user is a member
        memberships = OrganizationMembership.objects.filter(
            user=user
        ).select_related('organization')
        
        organization_ids = memberships.values_list('organization_id', flat=True)
        organizations = Organization.objects.filter(id__in=organization_ids).order_by('name')
        
        return list(organizations)


class SetActiveOrganization(graphene.Mutation):
    """
    Mutation to set user's active organization.
    
    Users can switch between organizations they belong to. This mutation
    sets the active organization for the current user session, which is
    required for performing organization-scoped operations.
    
    Args:
        organization_id: ID of the organization to set as active
        
    Returns:
        success: Boolean indicating if operation was successful
        organization: The active organization object
    """
    
    success = graphene.Boolean(
        required=True,
        description='Indicates if the operation was successful.'
    )
    organization = graphene.Field(
        OrganizationType,
        description='The organization that was set as active.'
    )
    
    class Arguments:
        """Input arguments for SetActiveOrganization mutation."""
        organization_id = graphene.Int(
            required=True,
            description='ID of the organization to set as active.'
        )
    
    @classmethod
    def mutate(cls, root, info, organization_id: int):
        """
        Set user's active organization.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            organization_id: ID of the organization
            
        Returns:
            SetActiveOrganization: Instance with success and organization
            
        Raises:
            GraphQLError: If authentication fails or user is not a member
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Permission check: User must be a member of the organization
        try:
            if not check_user_in_organization(user, organization_id):
                raise PermissionError(
                    f'User is not a member of organization {organization_id}.'
                )
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Verify organization exists
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise GraphQLError(
                f'Organization {organization_id} not found.',
                extensions={'code': 'NOT_FOUND'}
            )
        
        # Set active organization
        user.active_organization_id = organization_id
        user.save(update_fields=['active_organization_id'])
        
        return cls(success=True, organization=organization)


class InviteUserToOrganization(graphene.Mutation):
    """
    Mutation to invite a user to an organization (ADMIN only).
    
    This mutation allows organization administrators to add users to their
    organization and assign them a role (ADMIN or MEMBER). If the user
    already has a membership, their role will be updated.
    
    Args:
        organization_id: ID of the organization
        user_email: Email of the user to invite
        role: Role to assign (ADMIN or MEMBER)
        
    Returns:
        success: Boolean indicating if operation was successful
        membership: The created or updated membership object
    """
    
    success = graphene.Boolean(
        required=True,
        description='Indicates if the operation was successful.'
    )
    membership = graphene.Field(
        OrganizationMembershipType,
        description='The created or updated membership object.'
    )
    
    class Arguments:
        """Input arguments for InviteUserToOrganization mutation."""
        organization_id = graphene.Int(
            required=True,
            description='ID of the organization to invite user to.'
        )
        user_email = graphene.String(
            required=True,
            description='Email address of the user to invite.'
        )
        role = graphene.String(
            required=True,
            description='Role to assign (ADMIN or MEMBER).'
        )
    
    @classmethod
    def mutate(cls, root, info, organization_id: int, user_email: str, role: str):
        """
        Invite user to organization.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            organization_id: ID of the organization
            user_email: Email of the user to invite
            role: Role to assign
            
        Returns:
            InviteUserToOrganization: Instance with success and membership
            
        Raises:
            GraphQLError: If authentication fails, permission denied, or validation fails
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Permission check: Must be ADMIN of the organization
        try:
            require_organization_admin(user, organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Verify organization exists
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise GraphQLError(
                f'Organization {organization_id} not found.',
                extensions={'code': 'NOT_FOUND'}
            )
        
        # Get or create the user to invite
        try:
            invite_user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise GraphQLError(
                f'User with email {user_email} does not exist.',
                extensions={'code': 'USER_NOT_FOUND'}
            )
        
        # Validate role
        valid_roles = [OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.MEMBER]
        if role not in valid_roles:
            raise GraphQLError(
                f'Invalid role: {role}. Must be one of: {", ".join(valid_roles)}.',
                extensions={'code': 'INVALID_INPUT'}
            )
        
        # Create or update membership
        membership, created = OrganizationMembership.objects.get_or_create(
            user=invite_user,
            organization=organization,
            defaults={'role': role}
        )
        
        # Update role if membership already existed
        if not created and membership.role != role:
            membership.role = role
            membership.save(update_fields=['role'])
        
        return cls(success=True, membership=membership)


class Mutation(graphene.ObjectType):
    """
    Root mutation type for organizations.
    
    All organization-related mutations are aggregated here.
    """
    
    set_active_organization = SetActiveOrganization.Field(
        description='Set the active organization for the current user.'
    )
    invite_user_to_organization = InviteUserToOrganization.Field(
        description='Invite a user to an organization (ADMIN only).'
    )

