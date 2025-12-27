"""
MCP (Model Context Protocol) Server Layer.

This module implements the MCP server to expose document content as context.
The MCP server is clearly separated from GraphQL resolvers and LLM execution logic.

MCP (Model Context Protocol) is used to provide document context to the LLM
in a standardized, protocol-based manner. This ensures clean separation between
context preparation and LLM execution.

Architecture:
- MCPServer: Core MCP server that exposes document content
- MCPContextProvider: Bridge between business logic and MCP protocol
- Separation: MCP logic is separate from GraphQL resolvers and LLM service
"""
from typing import Dict, Any
from documents.models import Document


class MCPServer:
    """
    MCP Server for exposing document content as context.
    
    This server provides document content through MCP protocol,
    allowing LLM to consume context via MCP rather than manual prompt concatenation.
    
    The MCP server handles:
    1. Retrieving document data from the database
    2. Formatting document content according to MCP protocol standards
    3. Providing structured context that can be consumed by LLM services
    """
    
    @staticmethod
    def get_document_context(document_id: int) -> Dict[str, Any]:
        """
        Get document content as MCP context dictionary.
        
        Retrieves a document from the database and structures it as
        an MCP context dictionary with type, content, and metadata.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            Dict[str, Any]: Dictionary containing MCP-formatted document context
                - type: 'document_context' or 'error'
                - document_id: Document ID
                - title: Document title
                - content: Document content
                - metadata: Dictionary with organization_id and created_at
        """
        try:
            document = Document.objects.select_related('organization').get(id=document_id)
            return {
                'type': 'document_context',
                'document_id': document.id,
                'title': document.title,
                'content': document.content,
                'metadata': {
                    'organization_id': document.organization_id,
                    'organization_name': document.organization.name,
                    'created_at': document.created_at.isoformat(),
                    'created_by': document.created_by.email if document.created_by else None,
                }
            }
        except Document.DoesNotExist:
            return {
                'type': 'error',
                'message': f'Document {document_id} not found'
            }
    
    @staticmethod
    def format_context_for_mcp(context: Dict[str, Any]) -> str:
        """
        Format context dictionary into MCP protocol format string.
        
        This method ensures the context is properly structured for MCP consumption.
        The formatted string follows MCP protocol standards with clear structure
        and metadata.
        
        Args:
            context: Dictionary containing document context (from get_document_context)
            
        Returns:
            str: MCP-formatted context string ready for LLM consumption
        """
        if context.get('type') == 'document_context':
            metadata = context.get('metadata', {})
            return f"""Document Context (MCP):
Title: {context['title']}
Content:
{context['content']}

Metadata:
- Document ID: {context['document_id']}
- Organization ID: {metadata.get('organization_id')}
- Organization Name: {metadata.get('organization_name', 'N/A')}
- Created: {metadata.get('created_at')}
- Created By: {metadata.get('created_by', 'N/A')}
"""
        else:
            return context.get('message', 'Unknown context type')


class MCPContextProvider:
    """
    Context provider that interfaces with MCP server.
    
    This class bridges the gap between business logic and MCP protocol,
    ensuring clean separation of concerns. It provides a clean interface
    for retrieving document context via MCP without exposing implementation
    details to the calling code.
    
    Usage:
        provider = MCPContextProvider()
        context = provider.provide_document_context(document_id=1)
        # context is now a formatted MCP string ready for LLM
    """
    
    def __init__(self, mcp_server: MCPServer = None):
        """
        Initialize MCP context provider.
        
        Args:
            mcp_server: Optional MCPServer instance (creates new one if not provided)
        """
        self.mcp_server = mcp_server or MCPServer()
    
    def provide_document_context(self, document_id: int) -> str:
        """
        Provide document context via MCP.
        
        This method should be called when LLM needs document context.
        It ensures context is provided through MCP protocol, not through
        manual string concatenation. This maintains separation between:
        - MCP Server: Handles context retrieval and formatting
        - LLM Service: Handles LLM API communication
        - GraphQL Resolvers: Handle authentication and business logic
        
        Args:
            document_id: ID of the document to provide context for
            
        Returns:
            str: MCP-formatted context string ready for LLM consumption
            
        Raises:
            ValueError: If document context cannot be retrieved
        """
        context = self.mcp_server.get_document_context(document_id)
        
        if context.get('type') == 'error':
            raise ValueError(context.get('message', 'Failed to retrieve document context'))
        
        return self.mcp_server.format_context_for_mcp(context)

