"""
GraphQL schema for documents app.

This module provides GraphQL queries and mutations for document management
and AI-powered question answering. All permission checks are enforced at
the resolver level.
"""
import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.contrib.auth import get_user_model
from documents.models import Document, AIConversation
from organizations.permissions import (
    require_active_organization,
    require_organization_member,
    require_document_access,
    PermissionError
)


User = get_user_model()


class DocumentType(DjangoObjectType):
    """
    GraphQL type for Document model.
    
    Exposes document fields to the GraphQL API.
    """
    
    class Meta:
        model = Document
        fields = (
            'id',
            'title',
            'content',
            'organization',
            'created_by',
            'created_at',
            'updated_at'
        )
        description = 'Document type representing a document in an organization.'


class AIConversationType(DjangoObjectType):
    """
    GraphQL type for AIConversation model.
    
    Exposes AI conversation fields including question, answer, and metadata.
    """
    
    class Meta:
        model = AIConversation
        fields = (
            'id',
            'document',
            'user',
            'question',
            'answer',
            'created_at'
        )
        description = 'AI conversation type representing a Q&A session about a document.'


class Query(graphene.ObjectType):
    """
    Root Query type for documents.
    
    Provides queries for fetching document data and AI conversations.
    """
    
    documents = graphene.List(
        DocumentType,
        required=True,
        description='Get all documents in the user\'s active organization.'
    )
    document = graphene.Field(
        DocumentType,
        id=graphene.Int(required=True),
        description='Get a specific document by ID.'
    )
    ai_conversations = graphene.List(
        AIConversationType,
        document_id=graphene.Int(required=True),
        required=True,
        description='Get AI conversations for a specific document.'
    )
    
    def resolve_documents(self, info) -> list[Document]:
        """
        Resolve documents query.
        
        Returns all documents in the user's active organization.
        Requires user to have an active organization selected.
        
        Args:
            info: GraphQL resolver info object
            
        Returns:
            list[Document]: List of documents in active organization
            
        Raises:
            GraphQLError: If authentication fails or no active organization
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Permission check: Must have active organization
        try:
            organization_id = require_active_organization(user)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Permission check: Must be member of organization
        try:
            require_organization_member(user, organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Return documents in active organization
        documents = Document.objects.filter(
            organization_id=organization_id
        ).select_related('organization', 'created_by').order_by('-created_at')
        
        return list(documents)
    
    def resolve_document(self, info, id: int) -> Document:
        """
        Resolve document query by ID.
        
        Returns a specific document. User must be a member of the
        document's organization to access it.
        
        Args:
            info: GraphQL resolver info object
            id: Document ID
            
        Returns:
            Document: The requested document
            
        Raises:
            GraphQLError: If authentication fails, document not found, or permission denied
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Get document
        try:
            document = Document.objects.select_related(
                'organization',
                'created_by'
            ).get(id=id)
        except Document.DoesNotExist:
            raise GraphQLError(
                f'Document {id} not found.',
                extensions={'code': 'NOT_FOUND'}
            )
        
        # Permission check: User must be member of document's organization
        try:
            require_document_access(user, document.organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        return document
    
    def resolve_ai_conversations(self, info, document_id: int) -> list[AIConversation]:
        """
        Resolve AI conversations query.
        
        Returns all AI conversations for a specific document, ordered by
        creation date (newest first). User must be a member of the document's
        organization.
        
        Args:
            info: GraphQL resolver info object
            document_id: ID of the document
            
        Returns:
            list[AIConversation]: List of AI conversations for the document
            
        Raises:
            GraphQLError: If authentication fails, document not found, or permission denied
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Get document to verify it exists and check permissions
        try:
            document = Document.objects.select_related('organization').get(id=document_id)
        except Document.DoesNotExist:
            raise GraphQLError(
                f'Document {document_id} not found.',
                extensions={'code': 'NOT_FOUND'}
            )
        
        # Permission check: User must be member of document's organization
        try:
            require_document_access(user, document.organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Return conversations ordered by creation date (newest first)
        conversations = AIConversation.objects.filter(
            document_id=document_id
        ).select_related('document', 'user').order_by('-created_at')
        
        return list(conversations)


class CreateDocument(graphene.Mutation):
    """
    Mutation to create a document (ADMIN only).
    
    This mutation allows organization administrators to create new documents
    in their active organization. Only ADMIN users can create documents.
    
    Args:
        title: Document title (required)
        content: Document content (required)
        
    Returns:
        document: The created document object
    """
    
    document = graphene.Field(
        DocumentType,
        description='The created document object.'
    )
    
    class Arguments:
        """Input arguments for CreateDocument mutation."""
        title = graphene.String(
            required=True,
            description='Title of the document.'
        )
        content = graphene.String(
            required=True,
            description='Content/text of the document.'
        )
    
    @classmethod
    def mutate(cls, root, info, title: str, content: str):
        """
        Create a new document.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            title: Document title
            content: Document content
            
        Returns:
            CreateDocument: Instance with created document
            
        Raises:
            GraphQLError: If authentication fails, permission denied, or validation fails
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Permission check: Must have active organization
        try:
            organization_id = require_active_organization(user)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Permission check: Must be ADMIN
        try:
            require_organization_admin(user, organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Validate input
        if not title.strip():
            raise GraphQLError(
                'Document title cannot be empty.',
                extensions={'code': 'INVALID_INPUT'}
            )
        
        if not content.strip():
            raise GraphQLError(
                'Document content cannot be empty.',
                extensions={'code': 'INVALID_INPUT'}
            )
        
        # Create document
        document = Document.objects.create(
            title=title.strip(),
            content=content.strip(),
            organization_id=organization_id,
            created_by=user
        )
        
        return cls(document=document)


class AskDocumentAIQuestion(graphene.Mutation):
    """
    Mutation to ask AI question about a document (ADMIN & MEMBER).
    
    This mutation allows users to ask questions about documents using AI.
    Both ADMIN and MEMBER roles can ask questions. The AI response is
    generated using MCP (Model Context Protocol) for context provision
    and stored for future reference.
    
    Args:
        document_id: ID of the document to ask about (required)
        question: User's question (required)
        
    Returns:
        conversation: The created AI conversation object
    """
    
    conversation = graphene.Field(
        AIConversationType,
        description='The created AI conversation with question and answer.'
    )
    
    class Arguments:
        """Input arguments for AskDocumentAIQuestion mutation."""
        document_id = graphene.Int(
            required=True,
            description='ID of the document to ask about.'
        )
        question = graphene.String(
            required=True,
            description='User\'s question about the document.'
        )
    
    @classmethod
    def mutate(cls, root, info, document_id: int, question: str):
        """
        Ask AI question about a document.
        
        Args:
            root: Root value (unused)
            info: GraphQL resolver info object
            document_id: ID of the document
            question: User's question
            
        Returns:
            AskDocumentAIQuestion: Instance with conversation
            
        Raises:
            GraphQLError: If authentication fails, permission denied, or LLM error
        """
        user = info.context.user
        
        if not user or not user.is_authenticated:
            raise GraphQLError(
                'Authentication required.',
                extensions={'code': 'UNAUTHORIZED'}
            )
        
        # Get document
        try:
            document = Document.objects.select_related('organization').get(id=document_id)
        except Document.DoesNotExist:
            raise GraphQLError(
                f'Document {document_id} not found.',
                extensions={'code': 'NOT_FOUND'}
            )
        
        # Permission check: User must be member of document's organization
        try:
            require_document_access(user, document.organization_id)
        except PermissionError as e:
            raise GraphQLError(
                str(e),
                extensions={'code': 'PERMISSION_DENIED'}
            )
        
        # Validate question
        if not question.strip():
            raise GraphQLError(
                'Question cannot be empty.',
                extensions={'code': 'INVALID_INPUT'}
            )
        
        # Call LLM service (which uses MCP for context)
        # Note: LLMService will be imported when implemented in next step
        try:
            from documents.llm_service import LLMService
            llm_service = LLMService()
            answer = llm_service.ask_question(document_id, question.strip())
        except ImportError:
            raise GraphQLError(
                'LLM service not yet implemented.',
                extensions={'code': 'NOT_IMPLEMENTED'}
            )
        except Exception as e:
            raise GraphQLError(
                f'Error calling LLM: {str(e)}',
                extensions={'code': 'LLM_ERROR'}
            )
        
        # Save conversation
        conversation = AIConversation.objects.create(
            document=document,
            user=user,
            question=question.strip(),
            answer=answer
        )
        
        return cls(conversation=conversation)


class Mutation(graphene.ObjectType):
    """
    Root mutation type for documents.
    
    All document-related mutations are aggregated here.
    """
    
    create_document = CreateDocument.Field(
        description='Create a new document (ADMIN only).'
    )
    ask_document_ai_question = AskDocumentAIQuestion.Field(
        description='Ask an AI question about a document (ADMIN & MEMBER).'
    )

