# JWT Authentication System

## Overview

The authentication system has been upgraded from the insecure `X-User-ID` header approach to a secure JWT (JSON Web Token) based system.

## Security Improvements

### Before (Insecure)
- Used `X-User-ID` header with raw user ID
- No cryptographic verification
- No token expiration
- Easily spoofable by setting any user ID

### After (Secure)
- JWT tokens with cryptographic signatures
- Token expiration (30 minutes by default)
- Bearer token authentication
- Cannot be forged without the secret key

## API Changes

### Login Endpoint
**POST /auth/login**

Request:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "your_username",
    "email": "user@example.com",
    "is_admin": false,
    "is_active": true
  },
  "expires_in": 1800
}
```

### Authentication
All authenticated endpoints now require the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### New Endpoints
**GET /auth/me** - Get current user information using JWT token
**POST /auth/refresh** - Refresh access token using refresh token

Request:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response (same as login):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {...},
  "expires_in": 1800
}
```

## Environment Variables

- `JWT_SECRET_KEY`: Secret key for signing tokens (change in production!)
- `JWT_EXPIRE_MINUTES`: Access token expiration time in minutes (default: 30)
- `JWT_REFRESH_EXPIRE_DAYS`: Refresh token expiration time in days (default: 7)

## Implementation Details

### Functions
- `get_current_user()`: Requires valid JWT token (raises 401 if missing/invalid)
- `get_current_user_optional()`: Optional authentication (returns None if no/invalid token)

### Token Structure
JWT tokens contain:
- `sub`: User ID (subject)
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `type`: Token type ("access" or "refresh")

## Migration Guide

### For API Clients
1. Call `/auth/login` to get JWT tokens
2. Store both `access_token` and `refresh_token` securely
3. Include `Authorization: Bearer <access_token>` header in all requests
4. Handle token expiration (401 response) by calling `/auth/refresh` with the refresh token
5. If refresh fails, re-authenticate with `/auth/login`

### For Frontend Applications
```javascript
// Login
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});
const { access_token, refresh_token } = await response.json();

// Store tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Use token in requests
const authHeaders = {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
};

// Make authenticated request with automatic refresh handling
// (The frontend automatically handles 401 responses and refreshes tokens)
const dataResponse = await fetch('/tree-items/123', {
  headers: authHeaders
});
```

## Security Best Practices

1. **Change the JWT secret key** in production
2. **Use HTTPS** to protect tokens in transit
3. **Store tokens securely** (consider secure storage alternatives to localStorage for sensitive apps)
4. **Handle token expiration** gracefully with automatic refresh
5. **Automatic token refresh** is now implemented for seamless user experience
6. **Proactive token renewal** happens before expiration to prevent interruptions
