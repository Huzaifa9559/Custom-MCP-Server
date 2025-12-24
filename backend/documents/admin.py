"""
Django admin configuration for documents app.

This module registers Document and AIConversation models with Django admin
and customizes the admin interface for document and conversation management.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Document, AIConversation


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Admin interface for Document model.
    
    Provides a comprehensive admin interface for managing documents,
    including viewing conversation statistics and content previews.
    """
    
    list_display = (
        'title',
        'organization',
        'created_by',
        'conversation_count_display',
        'created_at',
        'updated_at',
    )
    list_filter = ('organization', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'organization__name')
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'conversation_count_display',
        'content_preview',
    )
    
    fieldsets = (
        (_('Document Information'), {
            'fields': ('title', 'content', 'organization', 'created_by')
        }),
        (_('Statistics'), {
            'fields': ('conversation_count_display',),
            'classes': ('collapse',),
        }),
        (_('Preview'), {
            'fields': ('content_preview',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def conversation_count_display(self, obj: Document) -> str:
        """
        Display conversation count with color coding.
        
        Args:
            obj: Document instance
            
        Returns:
            str: Formatted conversation count
        """
        count = obj.conversation_count
        color = 'green' if count > 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    conversation_count_display.short_description = _('AI Conversations')
    conversation_count_display.admin_order_field = 'ai_conversations__count'
    
    def content_preview(self, obj: Document) -> str:
        """
        Display content preview in admin.
        
        Args:
            obj: Document instance
            
        Returns:
            str: Formatted content preview
        """
        preview = obj.content_preview(max_length=200)
        return format_html(
            '<div style="max-width: 600px; white-space: pre-wrap;">{}</div>',
            preview
        )
    content_preview.short_description = _('Content Preview')
    
    def get_queryset(self, request):
        """
        Optimize queryset by selecting related objects.
        
        Args:
            request: HTTP request object
            
        Returns:
            QuerySet: Optimized queryset
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('organization', 'created_by').prefetch_related('ai_conversations')


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """
    Admin interface for AIConversation model.
    
    Provides admin interface for viewing AI conversation history,
    including question and answer previews.
    """
    
    list_display = (
        'document',
        'user',
        'question_preview_display',
        'answer_preview_display',
        'created_at',
    )
    list_filter = ('created_at', 'document', 'document__organization')
    search_fields = (
        'question',
        'answer',
        'document__title',
        'user__email',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'question_preview_display', 'answer_preview_display')
    
    fieldsets = (
        (_('Conversation Information'), {
            'fields': ('document', 'user', 'question', 'answer')
        }),
        (_('Previews'), {
            'fields': ('question_preview_display', 'answer_preview_display'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def question_preview_display(self, obj: AIConversation) -> str:
        """
        Display question preview in admin.
        
        Args:
            obj: AIConversation instance
            
        Returns:
            str: Formatted question preview
        """
        preview = obj.question_preview(max_length=150)
        return format_html(
            '<div style="max-width: 600px; font-weight: bold; color: #0066cc;">{}</div>',
            preview
        )
    question_preview_display.short_description = _('Question Preview')
    
    def answer_preview_display(self, obj: AIConversation) -> str:
        """
        Display answer preview in admin.
        
        Args:
            obj: AIConversation instance
            
        Returns:
            str: Formatted answer preview
        """
        preview = obj.answer_preview(max_length=300)
        return format_html(
            '<div style="max-width: 600px; white-space: pre-wrap;">{}</div>',
            preview
        )
    answer_preview_display.short_description = _('Answer Preview')
    
    def get_queryset(self, request):
        """
        Optimize queryset by selecting related objects.
        
        Args:
            request: HTTP request object
            
        Returns:
            QuerySet: Optimized queryset
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('document', 'user', 'document__organization')
