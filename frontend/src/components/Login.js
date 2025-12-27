/**
 * Login component.
 * 
 * Handles user authentication via email and password.
 * Uses GraphQL token_auth mutation to obtain JWT token.
 */
import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import './Login.css';

const TOKEN_AUTH = gql`
  mutation TokenAuth($email: String!, $password: String!) {
    token_auth(email: $email, password: $password) {
      token
      user {
        id
        email
      }
    }
  }
`;

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const [tokenAuth, { loading }] = useMutation(TOKEN_AUTH, {
    onCompleted: (data) => {
      if (data.token_auth.token) {
        onLogin(data.token_auth.token);
      }
    },
    onError: (err) => {
      setError(err.message || 'Login failed');
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    tokenAuth({ variables: { email, password } });
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Document AI Assistant</h1>
        <h2>Login</h2>
        {error && <div className="error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;

