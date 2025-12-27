/**
 * Apollo Client configuration for GraphQL API.
 * 
 * This module sets up Apollo Client with JWT authentication support.
 * The client automatically includes the JWT token in the Authorization
 * header for all GraphQL requests.
 */
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

// HTTP link to GraphQL endpoint
const httpLink = createHttpLink({
  uri: process.env.REACT_APP_GRAPHQL_URL || 'http://localhost:8000/graphql/',
});

// Auth link to add JWT token to requests
const authLink = setContext((_, { headers }) => {
  // Get token from localStorage
  const token = localStorage.getItem('token');
  
  // Return headers with Authorization if token exists
  return {
    headers: {
      ...headers,
      Authorization: token ? `JWT ${token}` : '',
    }
  };
});

// Create Apollo Client instance
const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});

export default client;

