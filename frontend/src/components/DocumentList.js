/**
 * Document list component.
 * 
 * Displays list of documents in the active organization.
 * Allows creating new documents (ADMIN only) and selecting documents to view.
 */
import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import './DocumentList.css';

const GET_DOCUMENTS = gql`
  query GetDocuments {
    documents {
      id
      title
      content
      created_by {
        id
        email
      }
      created_at
    }
  }
`;

const CREATE_DOCUMENT = gql`
  mutation CreateDocument($title: String!, $content: String!) {
    create_document(title: $title, content: $content) {
      document {
        id
        title
        content
        created_at
      }
    }
  }
`;

function DocumentList({ onDocumentSelect, selectedDocumentId }) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  
  const { data, loading, error, refetch } = useQuery(GET_DOCUMENTS, {
    errorPolicy: 'all',
  });
  
  const [createDocument, { loading: creating }] = useMutation(CREATE_DOCUMENT, {
    onCompleted: () => {
      setShowCreateForm(false);
      setTitle('');
      setContent('');
      refetch();
    },
    onError: (err) => {
      alert(`Error creating document: ${err.message}`);
    }
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createDocument({ variables: { title, content } });
  };

  if (loading) return <div className="card loading">Loading documents...</div>;
  if (error) return <div className="card error">Error: {error.message}</div>;

  return (
    <div className="document-list">
      <div className="card">
        <div className="card-header">
          <h2>Documents</h2>
          <button onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? 'Cancel' : '+ New Document'}
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreate} className="create-form">
            <input
              type="text"
              placeholder="Document Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <textarea
              placeholder="Document Content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
            />
            <button type="submit" disabled={creating}>
              {creating ? 'Creating...' : 'Create Document'}
            </button>
          </form>
        )}

        <div className="document-items">
          {data?.documents?.length === 0 ? (
            <p className="empty-message">
              No documents. Create one to get started.
            </p>
          ) : (
            data?.documents?.map((doc) => (
              <div
                key={doc.id}
                className={`document-item ${selectedDocumentId === doc.id ? 'selected' : ''}`}
                onClick={() => onDocumentSelect(doc)}
              >
                <h3>{doc.title}</h3>
                <p className="document-meta">
                  Created: {new Date(doc.created_at).toLocaleDateString()}
                </p>
                <p className="document-preview">
                  {doc.content.substring(0, 100)}...
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentList;

