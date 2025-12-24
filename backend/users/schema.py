"""
GraphQL schema for user authentication.

This module provides GraphQL mutations for JWT-based authentication,
including login, token verification, and token refresh functionality.
"""
import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.contrib.auth import authenticate, get_user_model
import graphql_jwt
from graphql_jwt.decorators import login_required
from graphql_jwt.utils import jwt_encode, jwt_payload


User = get_user_model()


class UserType(DjangoObjectType):
    """
    GraphQL type for User model.
    
    Exposes user fields to the GraphQL API. Only includes safe fields
    that can be exposed publicly (id, email, username).
    """
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username')
        description = 'User type representing an authenticated user.'


class TokenAuth(graphene.Mutation):
    """
    Obtain JWT token for authentication using email and password.
    
    This mutation authenticates a user with their email and password,
    then returns a JWT token that can be used for subsequent authenticated
    requests. The token should be included in the Authorization header
    as "JWT <token>".
    
    Args:
        email: User's email address (required)
        password: User's password (required)
        
    Returns:
        token: JWT authentication token
        user: Authenticated user object
    """
    
    token = graphene.String(
        description='JWT token for authenticated requests.'
    )
    user = graphene.Field(
        UserType,
        description='Authenticated user object.'
    )
    
    class Arguments:
        """Input arguments for TokenAuth mutation."""
        email = graphene.String(
            required=True,
            description='User email address for authentication.'
        )
        password = graphene.String(
            required=True,
            description='User password for authentication.'
        )
    
    @classmethod
    def mutate(cls, root, info, email: str, password: str):
        """
        Authenticate user and generate JWT token.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            email: User's email address
            password: User's password
            
        Returns:
            TokenAuth: Instance with token and user
            
        Raises:
            GraphQLError: If authentication fails
        """
        # Authenticate user using email as username
        user = authenticate(
            request=info.context,
            username=email,
            password=password
        )
        
        if user is None:
            raise GraphQLError(
                'Invalid email or password.',
                extensions={'code': 'AUTHENTICATION_FAILED'}
            )
        
        if not user.is_active:
            raise GraphQLError(
                'User account is disabled.',
                extensions={'code': 'ACCOUNT_DISABLED'}
            )
        
        # Generate JWT token
        payload = jwt_payload(user, info.context)
        token = jwt_encode(payload)
        
        return cls(token=token, user=user)


class VerifyToken(graphene.Mutation):
    """
    Verify a JWT token and return the payload.
    
    This mutation can be used to verify if a token is still valid
    and get information about the authenticated user.
    """
    
    payload = graphene.JSONString(
        description='JWT token payload.'
    )
    
    class Arguments:
        """Input arguments for VerifyToken mutation."""
        token = graphene.String(
            required=True,
            description='JWT token to verify.'
        )
    
    @classmethod
    def mutate(cls, root, info, token: str):
        """
        Verify JWT token.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            token: JWT token to verify
            
        Returns:
            VerifyToken: Instance with token payload
        """
        # Use graphql_jwt's verify mutation
        return graphql_jwt.Verify.Field().mutate(root, info, token)


class RefreshToken(graphene.Mutation):
    """
    Refresh a JWT token to get a new token with extended expiration.
    
    This mutation generates a new JWT token from an existing valid token,
    useful for extending user sessions without requiring re-authentication.
    """
    
    token = graphene.String(
        description='New JWT token with extended expiration.'
    )
    payload = graphene.JSONString(
        description='JWT token payload.'
    )
    
    class Arguments:
        """Input arguments for RefreshToken mutation."""
        token = graphene.String(
            required=True,
            description='Current JWT token to refresh.'
        )
    
    @classmethod
    def mutate(cls, root, info, token: str):
        """
        Refresh JWT token.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            token: Current JWT token
            
        Returns:
            RefreshToken: Instance with new token and payload
        """
        # Use graphql_jwt's refresh mutation
        return graphql_jwt.Refresh.Field().mutate(root, info, token)


class Mutation(graphene.ObjectType):
    """
    Root mutation type for user authentication.
    
    All authentication-related mutations are aggregated here.
    """
    
    # Authentication mutations
    token_auth = TokenAuth.Field(
        description='Obtain JWT token using email and password.'
    )
    verify_token = graphql_jwt.Verify.Field(
        description='Verify JWT token validity.'
    )
    refresh_token = graphql_jwt.Refresh.Field(
        description='Refresh JWT token to extend session.'
    )

