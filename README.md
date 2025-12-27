# Multi-Tenant Document AI Assistant

A Django + React + GraphQL application that provides AI-powered document question answering with multi-tenant organization support, using MCP (Model Context Protocol) for context provision.

## Tech Stack

### Backend
- **Django 5.0.3** - Web framework
- **Graphene-Django 3.2.0** - GraphQL integration
- **PostgreSQL** - Database
- **django-graphql-jwt 0.4.0** - JWT authentication
- **MCP (Model Context Protocol)** - Document context exposure
- **OpenAI/Anthropic/Gemini** - LLM integration

### Frontend
- **React 18.2.0** - UI framework
- **Apollo Client 3.9.5** - GraphQL client
- **React Router DOM 6.22.3** - Routing

## Features

- **Multi-Tenant Architecture**: Users can belong to multiple organizations
- **Role-Based Access Control**: ADMIN and MEMBER roles with different permissions
- **JWT Authentication**: Secure token-based authentication
- **Document Management**: Create, view, and manage documents (ADMIN only)
- **AI Question Answering**: Ask questions about documents using LLM
- **MCP Integration**: Document context provided via Model Context Protocol
- **GraphQL API**: All operations via GraphQL (no REST APIs)

## Project Setup

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- LLM API key (OpenAI, Anthropic, or Gemini)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp ../env.example ../.env
   ```
   Edit `.env` file with your configuration:
   ```env
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   DB_NAME=documentai_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   JWT_SECRET_KEY=your-jwt-secret-key-here
   JWT_ALGORITHM=HS256
   LLM_API_KEY=your-llm-api-key-here
   LLM_PROVIDER=openai  # or anthropic, gemini
   LLM_MODEL=gpt-4-turbo-preview  # or claude-3-5-sonnet-20241022, gemini-pro
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

5. **Create PostgreSQL database:**
   ```sql
   CREATE DATABASE documentai_db;
   ```

6. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser (optional, for admin panel):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server:**
   ```bash
   python manage.py runserver
   ```
   Backend will be available at `http://localhost:8000`
   GraphQL playground available at `http://localhost:8000/graphql/`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm start
   ```
   Frontend will be available at `http://localhost:3000`

## Authentication Flow

### JWT Authentication

The application uses JWT-based authentication with the following flow:

1. **Login**: User provides email and password via `token_auth` mutation
2. **Token Generation**: Backend validates credentials and returns JWT token
3. **Token Storage**: Frontend stores token in localStorage
4. **Request Authentication**: Apollo Client automatically includes token in `Authorization: JWT <token>` header
5. **Token Validation**: GraphQL middleware (`JSONWebTokenMiddleware`) extracts and validates token, setting `info.context.user`

### GraphQL Authentication Mutation

```graphql
mutation {
  token_auth(email: "user@example.com", password: "password123") {
    token
    user {
      id
      email
    }
  }
}
```

### Authentication Middleware

JWT authentication is handled by:
- **Backend**: `graphql_jwt.middleware.JSONWebTokenMiddleware` - Extracts JWT from Authorization header
- **Backend**: `graphql_jwt.backends.JSONWebTokenBackend` - Validates JWT and sets `request.user`
- **Frontend**: Apollo Client `authLink` - Adds JWT token to all requests

## Permission Handling Strategy

### Organization-Based Access Control

All permissions are enforced **at the GraphQL resolver level**, not in the frontend. The permission system is based on:

1. **Organization Membership**: Users must be members of an organization to access its resources
2. **Active Organization**: Users select an active organization to work within
3. **Role-Based Permissions**: Two roles with different capabilities:
   - **ADMIN**: Can create/manage documents, invite users
   - **MEMBER**: Can read documents, ask AI questions

### Permission Enforcement Points

All GraphQL resolvers check permissions before returning data:

#### Document Queries
- `documents`: Requires active organization membership
- `document(id)`: Requires membership in document's organization
- `aiConversations(documentId)`: Requires membership in document's organization

#### Document Mutations
- `create_document`: Requires ADMIN role in active organization
- `ask_document_ai_question`: Requires MEMBER or ADMIN role in document's organization

#### Organization Mutations
- `invite_user_to_organization`: Requires ADMIN role in target organization
- `set_active_organization`: Requires membership in target organization

### Permission Utility Functions

Located in `backend/organizations/permissions.py`:

- `require_active_organization(user)`: Ensures user has selected an active organization
- `require_organization_member(user, org_id)`: Ensures user is a member
- `require_organization_admin(user, org_id)`: Ensures user is an ADMIN
- `get_user_role_in_organization(user, org_id)`: Returns user's role

All permission functions raise `PermissionError` which is caught and converted to `GraphQLError` in resolvers, ensuring proper error responses.

## MCP Implementation Approach

### Model Context Protocol (MCP) Overview

MCP is used to provide document context to the LLM in a standardized, protocol-based manner. The implementation ensures clean separation between context preparation and LLM execution.

### MCP Architecture

The MCP implementation consists of three layers:

1. **MCP Server Layer** (`backend/documents/mcp_server.py`):
   - `MCPServer`: Core MCP server that exposes document content
   - `get_document_context(document_id)`: Retrieves document and formats as MCP context
   - `format_context_for_mcp(context)`: Formats context dictionary into MCP protocol format

2. **MCP Context Provider** (`backend/documents/mcp_server.py`):
   - `MCPContextProvider`: Bridge between business logic and MCP protocol
   - `provide_document_context(document_id)`: Provides document context via MCP

3. **LLM Service Integration** (`backend/documents/llm_service.py`):
   - `LLMService`: Integrates with LLM providers
   - Uses `MCPContextProvider` to get context (not manual string concatenation)

### How LLM Context is Passed

The context flow follows this pattern:

```
User Question → GraphQL Resolver → LLMService.ask_question()
  → MCPContextProvider.provide_document_context()
    → MCPServer.get_document_context()
      → Document Model (database)
    → MCPServer.format_context_for_mcp()
  → LLM Provider (OpenAI/Anthropic/Gemini) with MCP-formatted context
```

### Key Principles

1. **No Manual Concatenation**: Context is never manually concatenated into prompts. All context passes through MCP formatting.

2. **Separation of Concerns**:
   - MCP Server: Handles context retrieval and formatting
   - LLM Service: Handles LLM API communication
   - GraphQL Resolvers: Handle authentication and business logic

3. **MCP Protocol Compliance**: Context is formatted according to MCP protocol standards with proper structure:
   ```
   Document Context (MCP):
   Title: <title>
   Content:
   <content>
   
   Metadata:
   - Document ID: <id>
   - Organization ID: <org_id>
   - Created: <timestamp>
   ```

### Example MCP Context

When a user asks a question about document ID 1:

```python
# MCPContextProvider retrieves context via MCP
context = mcp_provider.provide_document_context(document_id=1)

# Context is formatted as:
"""
Document Context (MCP):
Title: Example Document
Content:
This is the document content...

Metadata:
- Document ID: 1
- Organization ID: 1
- Created: 2024-01-01T00:00:00
"""

# This formatted context is then passed to LLM
# (not manually concatenated)
```

### MCP Code Location

- **MCP Server**: `backend/documents/mcp_server.py`
- **LLM Service (uses MCP)**: `backend/documents/llm_service.py`
- **GraphQL Resolver (calls LLM Service)**: `backend/documents/schema.py` (AskDocumentAIQuestion mutation)

## GraphQL API

### Queries

#### Get Organizations
```graphql
query {
  organizations {
    id
    name
    created_at
  }
}
```

#### Get Documents
```graphql
query {
  documents {
    id
    title
    content
    created_at
  }
}
```

#### Get Document by ID
```graphql
query {
  document(id: 1) {
    id
    title
    content
    created_at
  }
}
```

#### Get AI Conversations
```graphql
query {
  ai_conversations(documentId: 1) {
    id
    question
    answer
    created_at
  }
}
```

### Mutations

#### Create Document (ADMIN only)
```graphql
mutation {
  create_document(title: "My Document", content: "Document content...") {
    document {
      id
      title
      content
    }
  }
}
```

#### Ask Document AI Question (ADMIN & MEMBER)
```graphql
mutation {
  ask_document_ai_question(documentId: 1, question: "What is this document about?") {
    conversation {
      id
      question
      answer
      created_at
    }
  }
}
```

#### Invite User to Organization (ADMIN only)
```graphql
mutation {
  invite_user_to_organization(
    organizationId: 1
    userEmail: "user@example.com"
    role: "MEMBER"
  ) {
    success
    membership {
      id
      role
    }
  }
}
```

#### Set Active Organization
```graphql
mutation {
  set_active_organization(organizationId: 1) {
    success
    organization {
      id
      name
    }
  }
}
```

## Security Considerations

### Environment Variables

- **Never commit `.env` file** - It's in `.gitignore`
- All secrets loaded from environment variables
- Use `env.example` as template

### API Key Management

- LLM API keys stored in environment variables
- Candidate must use their own API key
- No hardcoded secrets in codebase

### Permission Enforcement

- All permissions enforced at resolver level
- Frontend permissions are for UX only, not security
- Unauthorized access returns GraphQL errors (not silent failures)

## Database Models

### User
- Extends Django's AbstractUser
- Email as username
- `active_organization_id`: Currently selected organization

### Organization
- Multi-tenant container
- Has many documents and memberships

### OrganizationMembership
- Links users to organizations
- Roles: ADMIN, MEMBER
- Unique constraint on (user, organization)

### Document
- Belongs to an organization
- Has title and content
- Tracks creator

### AIConversation
- Links questions/answers to documents
- Stores question, answer, and timestamp
- Ordered by creation date (newest first)

## Testing the Application

### 1. Create Users and Organizations

Use Django admin or GraphQL mutations:

```graphql
# First, create a user via Django admin or script
# Then login
mutation {
  token_auth(email: "admin@example.com", password: "password") {
    token
  }
}

# Set active organization (after being invited)
mutation {
  set_active_organization(organizationId: 1) {
    success
  }
}
```

### 2. Create Documents (as ADMIN)

```graphql
mutation {
  create_document(
    title: "Project Documentation"
    content: "This document contains important information about the project..."
  ) {
    document {
      id
      title
    }
  }
}
```

### 3. Ask AI Questions

```graphql
mutation {
  ask_document_ai_question(
    documentId: 1
    question: "Summarize the key points"
  ) {
    conversation {
      question
      answer
    }
  }
}
```

## Project Structure

```
assignment/
├── backend/
│   ├── config/           # Django settings and main schema
│   ├── users/            # User model and auth schema
│   ├── organizations/    # Organization models, permissions, schema
│   ├── documents/        # Document models, MCP server, LLM service, schema
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── apollo-client.js
│   │   └── App.js
│   └── package.json
├── requirements.txt
├── env.example
├── .gitignore
└── README.md
```

## Troubleshooting

### JWT Authentication Not Working

- Verify token is being sent in `Authorization: JWT <token>` format
- Check `JWT_SECRET_KEY` in `.env` matches the key used to sign tokens
- Ensure `JSONWebTokenMiddleware` is in `GRAPHENE.MIDDLEWARE`

### LLM API Errors

- Verify `LLM_API_KEY` is set in `.env`
- Check API key is valid for selected provider
- Ensure sufficient API credits/quota

### Permission Errors

- Ensure user has selected an active organization
- Verify user is a member of the organization
- Check user's role matches required permission level

### Database Connection Issues

- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists: `CREATE DATABASE documentai_db;`

## License

This project is created for evaluation purposes.

