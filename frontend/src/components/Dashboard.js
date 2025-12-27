/**
 * Dashboard component.
 * 
 * Main application dashboard showing organization selector,
 * document list, and document viewer.
 */
import React, { useState } from 'react';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import OrganizationSelector from './OrganizationSelector';
import DocumentList from './DocumentList';
import DocumentViewer from './DocumentViewer';
import './Dashboard.css';

const GET_ORGANIZATIONS = gql`
  query GetOrganizations {
    organizations {
      id
      name
    }
  }
`;

function Dashboard({ onLogout }) {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const { data: orgData, loading: orgLoading, refetch: refetchOrgs } = useQuery(GET_ORGANIZATIONS);

  return (
    <div className="dashboard">
      <div className="header">
        <h1>Document AI Assistant</h1>
        <div className="header-actions">
          <OrganizationSelector
            organizations={orgData?.organizations || []}
            loading={orgLoading}
            onOrganizationChanged={refetchOrgs}
          />
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="sidebar">
          <DocumentList
            onDocumentSelect={setSelectedDocument}
            selectedDocumentId={selectedDocument?.id}
          />
        </div>
        <div className="main-content">
          {selectedDocument ? (
            <DocumentViewer
              document={selectedDocument}
              onClose={() => setSelectedDocument(null)}
            />
          ) : (
            <div className="empty-state">
              <p>Select a document to view and ask questions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

