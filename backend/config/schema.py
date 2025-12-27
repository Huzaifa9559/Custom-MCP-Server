"""
Main GraphQL schema module.

This module aggregates and combines all GraphQL schemas from different apps:
- users: Authentication mutations
- organizations: Organization queries and mutations
- documents: Document queries and AI conversation mutations

The schema follows the GraphQL schema design pattern where queries are read-only
operations and mutations are write operations.
"""
import graphene
from users.schema import Mutation as UserMutation
from organizations.schema import Query as OrganizationQuery, Mutation as OrganizationMutation
from documents.schema import Query as DocumentQuery, Mutation as DocumentMutation


class Query(
    OrganizationQuery,
    DocumentQuery,
    graphene.ObjectType
):
    """
    Root Query type for the GraphQL API.
    
    All read operations (queries) are aggregated here from various apps.
    Includes organization and document queries.
    """
    pass


class Mutation(
    UserMutation,
    OrganizationMutation,
    DocumentMutation,
    graphene.ObjectType
):
    """
    Root Mutation type for the GraphQL API.
    
    All write operations (mutations) are aggregated here from various apps.
    Includes authentication, organization, and document mutations.
    """
    pass


# Create the GraphQL schema instance
# This is the entry point for all GraphQL operations
schema = graphene.Schema(query=Query, mutation=Mutation)

