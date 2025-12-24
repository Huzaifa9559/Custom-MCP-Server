"""
Documents app configuration.

This app handles document management and AI-powered question answering
using MCP (Model Context Protocol) for context provision.
"""
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Configuration for the documents application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = 'Documents'

