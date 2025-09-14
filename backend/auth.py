"""Authentication and authorization helpers"""

from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from enum import Enum
import os
import models
from models import User, TreeItem


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# Security
security = HTTPBearer()


class Permission(str, Enum):
    """Enum for permission types"""
    READ = "read"
    WRITE = "write"


class AuthService:
    """JWT-based authentication service"""
    
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
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """
    Get current user from JWT token
    
    Validates the JWT token from the Authorization header and returns the user.
    Returns None if token is invalid or user doesn't exist.
    """
    if not credentials:
        return None
    
    # Verify the token
    payload = AuthService.verify_token(credentials.credentials)
    if not payload:
        return None
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # Get user from database
    user = await AuthService.get_user_by_id(user_id)
    if not user or not user.is_active:
        return None
    
    return user


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """
    Get current user from JWT token (optional)
    
    Same as get_current_user but doesn't raise an error if no token is provided.
    Used for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    # Verify the token
    payload = AuthService.verify_token(credentials.credentials)
    if not payload:
        return None
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # Get user from database
    user = await AuthService.get_user_by_id(user_id)
    if not user or not user.is_active:
        return None
    
    return user


async def require_permission(
    tree_item: TreeItem,
    user: Optional[User],
    permission: Permission = Permission.READ
) -> None:
    """
    Check if user has permission on tree item
    
    Args:
        tree_item: The TreeItem to check permissions for
        user: Current user (None for anonymous)
        permission: Permission.READ or Permission.WRITE
    
    Raises:
        HTTPException: If permission is denied
    """
    print("User %s requires permission %s on tree item %s" % (user, permission, tree_item))

    if permission == Permission.READ:
        has_permission = await tree_item.can_read(user)
    elif permission == Permission.WRITE:
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
                detail=f"Permission denied: insufficient {permission.value} permissions"
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
