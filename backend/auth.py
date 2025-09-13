"""Authentication and authorization helpers"""

from fastapi import HTTPException, Depends, Header
from typing import Optional
import models
from models import User, TreeItem


class AuthService:
    """Simple authentication service"""
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return await User.get(id=user_id)
        except Exception:
            return None
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return await User.get(username=username)
        except Exception:
            return None
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await AuthService.get_user_by_username(username)
        if user and user.is_active and user.check_password(password):
            return user
        return None


async def get_current_user(x_user_id: Optional[str] = Header(None)) -> Optional[User]:
    """
    Simple authentication via X-User-ID header
    
    This is a basic implementation. In production, you would use proper
    JWT tokens or session-based authentication.
    """
    if not x_user_id:
        return None
    
    user = await AuthService.get_user_by_id(x_user_id)
    if not user or not user.is_active:
        return None
    
    return user


async def require_permission(
    tree_item: TreeItem,
    user: Optional[User],
    permission: str = "read"
) -> None:
    """
    Check if user has permission on tree item
    
    Args:
        tree_item: The TreeItem to check permissions for
        user: Current user (None for anonymous)
        permission: "read" or "write"
    
    Raises:
        HTTPException: If permission is denied
    """
    if permission == "read":
        has_permission = await tree_item.can_read(user)
    elif permission == "write":
        has_permission = await tree_item.can_write(user)
    else:
        raise ValueError(f"Invalid permission type: {permission}")
    
    if not has_permission:
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: insufficient {permission} permissions"
            )


async def require_admin(user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Require admin user
    
    Raises:
        HTTPException: If user is not authenticated or not admin
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return user
