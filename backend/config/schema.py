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


class Query(
    OrganizationQuery,
    graphene.ObjectType
):
    """
    Root Query type for the GraphQL API.
    
    All read operations (queries) are aggregated here from various apps.
    Currently includes organization queries.
    """
    pass


class Mutation(
    UserMutation,
    OrganizationMutation,
    graphene.ObjectType
):
    """
    Root Mutation type for the GraphQL API.
    
    All write operations (mutations) are aggregated here from various apps.
    Currently includes authentication mutations and organization mutations.
    """
    pass


# Create the GraphQL schema instance
# This is the entry point for all GraphQL operations
schema = graphene.Schema(query=Query, mutation=Mutation)

