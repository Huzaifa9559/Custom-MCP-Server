"""
URL configuration for Document AI Assistant project.

This module defines the URL routing for the application:
- /admin/: Django admin interface
- /graphql/: GraphQL API endpoint with GraphiQL IDE
"""
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

# URL patterns
# Note: GraphQL endpoint uses csrf_exempt because JWT tokens handle authentication
# GraphiQL is enabled for development - should be disabled in production
urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

