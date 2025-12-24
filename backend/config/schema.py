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


class Query(graphene.ObjectType):
    """
    Root Query type for the GraphQL API.
    
    All read operations (queries) are aggregated here from various apps.
    Currently empty - will be extended as schemas are added from other apps.
    """
    pass


class Mutation(
    UserMutation,
    graphene.ObjectType
):
    """
    Root Mutation type for the GraphQL API.
    
    All write operations (mutations) are aggregated here from various apps.
    Currently includes authentication mutations from users app.
    """
    pass


# Create the GraphQL schema instance
# This is the entry point for all GraphQL operations
schema = graphene.Schema(query=Query, mutation=Mutation)

