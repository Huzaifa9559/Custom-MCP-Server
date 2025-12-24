"""
Document models.

This module contains models for document management and AI-powered
question answering functionality. Documents are organization-scoped,
enabling multi-tenant document isolation.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization


User = get_user_model()


class Document(models.Model):
    """
    Document model belonging to an organization.
    
    Documents represent the core entities that users can manage and query
    using AI. Each document belongs to a specific organization, ensuring
    proper multi-tenant data isolation. Documents can only be created by
    ADMIN users, but can be read by all members.
    
    Attributes:
        title: Document title (required)
        content: Document content/text (required)
        organization: Foreign key to Organization (required)
        created_by: User who created the document (nullable for data integrity)
        created_at: Timestamp when the document was created
        updated_at: Timestamp when the document was last updated
    """
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Document title.'),
    )
    content = models.TextField(
        _('content'),
        help_text=_('Document content/text.'),
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text=_('Organization this document belongs to.'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_documents',
        help_text=_('User who created this document.'),
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('Timestamp when the document was created.'),
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('Timestamp when the document was last updated.'),
    )
    
    class Meta:
        """Meta options for the Document model."""
        db_table = 'documents_document'
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['created_by']),
            models.Index(fields=['title']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the document."""
        return f'{self.title} ({self.organization.name})'
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation of the document."""
        return f'<Document: {self.title}@{self.organization.name}>'
    
    @property
    def conversation_count(self) -> int:
        """
        Get the number of AI conversations for this document.
        
        Returns:
            int: Number of AI conversations
        """
        return self.ai_conversations.count()
    
    @property
    def content_preview(self, max_length: int = 100) -> str:
        """
        Get a preview of the document content.
        
        Args:
            max_length: Maximum length of the preview (default: 100)
            
        Returns:
            str: Content preview truncated to max_length
        """
        if len(self.content) <= max_length:
            return self.content
        return f'{self.content[:max_length]}...'


class AIConversation(models.Model):
    """
    AI conversation entries for document question answering.
    
    This model stores the history of AI-powered Q&A sessions for documents.
    Each conversation entry links a question, AI-generated answer, document,
    and user together, enabling conversation history tracking and retrieval.
    
    Attributes:
        document: Foreign key to Document (required)
        user: User who asked the question (required)
        question: User's question (required)
        answer: AI-generated answer (required)
        created_at: Timestamp when the conversation was created
    """
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        help_text=_('Document this conversation is about.'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        help_text=_('User who asked this question.'),
    )
    question = models.TextField(
        _('question'),
        help_text=_('User\'s question about the document.'),
    )
    answer = models.TextField(
        _('answer'),
        help_text=_('AI-generated answer to the question.'),
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('Timestamp when the conversation was created.'),
    )
    
    class Meta:
        """Meta options for the AIConversation model."""
        db_table = 'documents_ai_conversation'
        verbose_name = _('AI conversation')
        verbose_name_plural = _('AI conversations')
        ordering = ['-created_at']  # Most recent first
        indexes = [
            models.Index(fields=['document', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the conversation."""
        question_preview = self.question[:50] + '...' if len(self.question) > 50 else self.question
        return f'Q: {question_preview} ({self.document.title})'
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation of the conversation."""
        return f'<AIConversation: {self.user.email}@{self.document.id}({self.created_at})>'
    
    @property
    def question_preview(self, max_length: int = 100) -> str:
        """
        Get a preview of the question.
        
        Args:
            max_length: Maximum length of the preview (default: 100)
            
        Returns:
            str: Question preview truncated to max_length
        """
        if len(self.question) <= max_length:
            return self.question
        return f'{self.question[:max_length]}...'
    
    @property
    def answer_preview(self, max_length: int = 200) -> str:
        """
        Get a preview of the answer.
        
        Args:
            max_length: Maximum length of the preview (default: 200)
            
        Returns:
            str: Answer preview truncated to max_length
        """
        if len(self.answer) <= max_length:
            return self.answer
        return f'{self.answer[:max_length]}...'
