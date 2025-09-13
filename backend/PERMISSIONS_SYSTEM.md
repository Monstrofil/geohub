# User, Roles, and Permissions System

## Overview

I've implemented a simple but effective Linux-style permissions system for TreeItems. This provides user authentication, group management, and granular read/write permissions on files and collections.

## Components

### 1. User Management
- **User Model**: Username, email, password (hashed with salt), admin flag
- **Password Security**: SHA-512 hashing with random salts
- **Admin Users**: Can manage other users and override permissions

### 2. Group Management  
- **Group Model**: Name, description, many-to-many relationship with users
- **Group Membership**: Users can belong to multiple groups
- **Default Groups**: "administrators" and "users" created by migration

### 3. Linux-Style Permissions
Each TreeItem has:
- **Owner User**: The user who owns the item
- **Owner Group**: The group that owns the item  
- **Permissions**: Integer using Linux octal format (e.g., 0o644)
  - Owner permissions: read (400), write (200)
  - Group permissions: read (040), write (020)
  - Other permissions: read (004), write (002)
  - Execute bit not used (our use case doesn't need it)

### 4. Permission Checking
- `can_read(user)`: Check if user can read the item
- `can_write(user)`: Check if user can write/modify the item
- `get_permission_string()`: Get human-readable permissions like "rw-rw-r--"

## API Endpoints

### Authentication
- `POST /auth/login`: Login with username/password
- `POST /auth/users`: Create new user (admin only)
- `GET /auth/users`: List all users (admin only)
- `POST /auth/groups`: Create new group (admin only)
- `GET /auth/groups`: List all groups (admin only)
- `POST /auth/groups/{group_id}/members/{user_id}`: Add user to group (admin only)
- `DELETE /auth/groups/{group_id}/members/{user_id}`: Remove user from group (admin only)

### Permissions Management
- `PUT /tree-items/{item_id}/permissions`: Update item ownership and permissions

### Updated Endpoints with Permission Checks
- `GET /tree-items/{item_id}`: Now requires read permission
- `PUT /tree-items/{item_id}`: Now requires write permission  
- `DELETE /tree-items/{item_id}`: Now requires write permission
- `POST /files`: Sets ownership to current user on upload

## Usage Examples

### 1. Authentication
Send authentication via `X-User-ID` header (simple approach for now):
```http
X-User-ID: user-uuid-here
```

### 2. Default Admin User
The migration creates a default admin user:
- **Username**: admin
- **Email**: admin@tagger.local
- **Password**: admin123
- **Is Admin**: true

### 3. Permission Values
Common permission values:
- `0o644` (420 decimal): Owner read/write, group read, others read
- `0o600` (384 decimal): Owner read/write only
- `0o666` (438 decimal): Everyone can read/write
- `0o640` (416 decimal): Owner read/write, group read, others nothing

### 4. Setting Permissions
```json
PUT /tree-items/{item_id}/permissions
{
  "owner_user_id": "uuid-of-user",
  "owner_group_id": "uuid-of-group", 
  "permissions": 420
}
```

## Database Migration

Run the migration to create the new tables and fields:
```bash
# The migration file is: backend/migrations/models/5_20250913190000_add_users_permissions.py
```

## Security Notes

1. **Simple Authentication**: Currently uses X-User-ID header. In production, implement proper JWT tokens or session-based auth.

2. **Password Security**: Uses SHA-512 with random salts. Consider upgrading to bcrypt/scrypt for production.

3. **Default Permissions**: New files get 0o644 (owner read/write, others read) by default.

4. **Admin Override**: Admin users can read/write any item regardless of permissions.

5. **Anonymous Access**: Items can be accessed without authentication if "other" permissions allow it.

## Benefits

- **Familiar Model**: Linux-style permissions are well understood
- **Granular Control**: Separate read/write permissions for owner/group/others
- **Simple Implementation**: Only 2 bits needed (read/write), no execute complexity
- **Scalable**: Works for individual users, teams, and public access
- **Backward Compatible**: Existing items continue to work (with default permissions)

This provides a solid foundation for access control that can be extended as needed.
