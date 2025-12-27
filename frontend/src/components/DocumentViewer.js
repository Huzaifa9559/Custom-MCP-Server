/**
 * Document viewer component.
 * 
 * Displays document content and allows asking AI questions.
 * Shows AI conversation history for the document.
 */
import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import './DocumentViewer.css';

const GET_DOCUMENT = gql`
  query GetDocument($id: Int!) {
    document(id: $id) {
      id
      title
      content
      created_at
    }
  }
`;

const GET_AI_CONVERSATIONS = gql`
  query GetAIConversations($documentId: Int!) {
    ai_conversations(documentId: $documentId) {
      id
      question
      answer
      created_at
    }
  }
`;

const ASK_DOCUMENT_AI_QUESTION = gql`
  mutation AskDocumentAIQuestion($documentId: Int!, $question: String!) {
    ask_document_ai_question(documentId: $documentId, question: $question) {
      conversation {
        id
        question
        answer
        created_at
      }
    }
  }
`;

function DocumentViewer({ document, onClose }) {
  const [question, setQuestion] = useState('');
  
  const [askQuestion, { loading: asking }] = useMutation(ASK_DOCUMENT_AI_QUESTION, {
    onCompleted: () => {
      setQuestion('');
      refetchConversations();
    },
    onError: (err) => {
      alert(`Error asking question: ${err.message}`);
    }
  });

  const { data: docData, loading: docLoading } = useQuery(GET_DOCUMENT, {
    variables: { id: document.id },
    skip: !document.id,
    errorPolicy: 'all',
  });

  const { data: conversationsData, loading: conversationsLoading, refetch: refetchConversations } = useQuery(
    GET_AI_CONVERSATIONS,
    {
      variables: { documentId: document.id },
      skip: !document.id,
      errorPolicy: 'all',
    }
  );

  const handleAskQuestion = (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    askQuestion({ variables: { documentId: document.id, question } });
  };

  const displayDoc = docData?.document || document;

  return (
    <div className="document-viewer">
      <div className="card">
        <div className="viewer-header">
          <h2>{displayDoc.title}</h2>
          <button onClick={onClose} className="close-btn">Close</button>
        </div>

        <div className="document-content">
          <h3>Content</h3>
          <div className="content-text">
            {docLoading ? 'Loading...' : displayDoc.content}
          </div>
        </div>

        <div className="ai-questions-section">
          <h3>Ask AI Questions</h3>
          <form onSubmit={handleAskQuestion}>
            <textarea
              placeholder="Ask a question about this document..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={asking}
            />
            <button type="submit" disabled={asking || !question.trim()}>
              {asking ? 'Asking...' : 'Ask Question'}
            </button>
          </form>
        </div>

        <div className="conversations-section">
          <h3>Previous Questions & Answers</h3>
          {conversationsLoading ? (
            <div className="loading">Loading conversations...</div>
          ) : conversationsData?.ai_conversations?.length === 0 ? (
            <p className="empty-message">
              No questions asked yet. Ask a question above to get started.
            </p>
          ) : (
            <div className="conversations-list">
              {conversationsData?.ai_conversations?.map((conv) => (
                <div key={conv.id} className="conversation-item">
                  <div className="question">
                    <strong>Q:</strong> {conv.question}
                  </div>
                  <div className="answer">
                    <strong>A:</strong> {conv.answer}
                  </div>
                  <div className="conversation-meta">
                    {new Date(conv.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentViewer;

