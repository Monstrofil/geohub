# Permission Bits System

## Overview

The system now includes a Linux-style permission bits method that returns read, write, and execute permissions for any user on any tree item.

## Core Features

### Permission Enum
```python
from auth import Permission

# Usage in require_permission calls
await require_permission(item, user, Permission.READ)
await require_permission(item, user, Permission.WRITE)
```

The `Permission` enum provides:
- `Permission.READ` - Read permission
- `Permission.WRITE` - Write permission

This replaces the previous string-based approach and provides type safety.

### Permission Bits Method

```python
# Get permission bits for a user on a tree item
read, write, execute = await tree_item.get_permission_bits(user)

# For anonymous users
read, write, execute = await tree_item.get_permission_bits(None)
```

### Linux-Style Permission Checking

The system follows Linux permission model:

#### Permission Structure (octal format like 0o764)
- **Owner permissions** (first digit): User who owns the item
- **Group permissions** (second digit): Members of the owner group  
- **Other permissions** (third digit): Everyone else

#### Permission Bits (per digit)
- **4 (read)**: Can view/read the item
- **2 (write)**: Can modify/delete the item
- **1 (execute)**: Currently dummy/placeholder for future use

#### Examples
- `0o644`: Owner can read/write, group can read, others can read
- `0o600`: Owner can read/write, no access for group/others
- `0o755`: Owner can read/write/execute, group and others can read/execute

## Permission Resolution Order

1. **Admin users**: Always get full permissions (True, True, True)
2. **Owner check**: If user owns the item, use owner permissions
3. **Group check**: If user is in owner group, use group permissions  
4. **Other permissions**: Fall back to "other" permissions
5. **Anonymous users**: Always use "other" permissions

## API Integration

The `require_permission` function now uses the Permission enum:

```python
# Check read permission (default)
await require_permission(item, current_user)
await require_permission(item, current_user, Permission.READ)

# Check write permission
await require_permission(item, current_user, Permission.WRITE)
```

## Example Usage

```python
from auth import Permission, get_user_permission_bits

# In an endpoint
async def check_permissions(item_id: str, current_user: User):
    item = await TreeItem.get(id=item_id)
    
    # Method 1: Use the convenience function
    read, write, execute = await get_user_permission_bits(item, current_user)
    
    # Method 2: Use the model method directly
    read, write, execute = await item.get_permission_bits(current_user)
    
    # Method 3: Use existing permission checks
    await require_permission(item, current_user, Permission.READ)
    
    return {
        "can_read": read,
        "can_write": write, 
        "can_execute": execute
    }
```

## Permission Scenarios

### Scenario 1: File Owner
```python
# User owns file with permissions 0o644
read, write, execute = await item.get_permission_bits(owner_user)
# Returns: (True, True, False)
```

### Scenario 2: Group Member
```python
# User in owner group, file has permissions 0o764
read, write, execute = await item.get_permission_bits(group_user)  
# Returns: (True, True, False) - group has rw-
```

### Scenario 3: Other User
```python
# Regular user, file has permissions 0o644
read, write, execute = await item.get_permission_bits(other_user)
# Returns: (True, False, False) - others have r--
```

### Scenario 4: Anonymous User
```python
# No user provided, file has permissions 0o644
read, write, execute = await item.get_permission_bits(None)
# Returns: (True, False, False) - others have r--
```

### Scenario 5: Admin User
```python
# Admin user always gets full permissions regardless of file permissions
read, write, execute = await item.get_permission_bits(admin_user)
# Returns: (True, True, True)
```
