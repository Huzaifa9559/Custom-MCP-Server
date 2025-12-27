/**
 * Organization selector component.
 * 
 * Allows users to switch between organizations they belong to.
 * Uses set_active_organization mutation to update active organization.
 */
import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';

const SET_ACTIVE_ORGANIZATION = gql`
  mutation SetActiveOrganization($organizationId: Int!) {
    set_active_organization(organizationId: $organizationId) {
      success
      organization {
        id
        name
      }
    }
  }
`;

function OrganizationSelector({ organizations, loading, onOrganizationChanged }) {
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [setActiveOrg, { loading: mutating }] = useMutation(SET_ACTIVE_ORGANIZATION, {
    onCompleted: () => {
      if (onOrganizationChanged) {
        onOrganizationChanged();
      }
      // Refresh page to reload data with new org context
      window.location.reload();
    },
    onError: (err) => {
      alert(`Error setting active organization: ${err.message}`);
    }
  });

  const handleChange = (e) => {
    const orgId = parseInt(e.target.value);
    if (orgId) {
      setSelectedOrgId(orgId);
      setActiveOrg({ variables: { organizationId: orgId } });
    }
  };

  if (loading) {
    return <div>Loading organizations...</div>;
  }

  if (organizations.length === 0) {
    return <div>No organizations available</div>;
  }

  return (
    <select
      value={selectedOrgId || ''}
      onChange={handleChange}
      disabled={mutating}
      className="organization-selector"
    >
      <option value="">Select Organization</option>
      {organizations.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </select>
  );
}

export default OrganizationSelector;

