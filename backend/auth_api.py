"""Authentication and authorization API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from pydantic import BaseModel

import models
from models import User
from auth import get_current_user, require_admin, AuthService, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(tags=["authentication"])


# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: models.User_Pydantic
    expires_in: int  # seconds


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False


class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionsUpdateRequest(BaseModel):
    owner_user_id: Optional[uuid.UUID] = None
    owner_group_id: Optional[uuid.UUID] = None
    permissions: Optional[int] = None  # Octal permissions like 0o644


# ======================
# AUTHENTICATION ENDPOINTS
# ======================

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with username and password and return JWT token"""
    user = await AuthService.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=models.User_Pydantic.model_validate(user),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds
    )


@router.get("/auth/me", response_model=models.User_Pydantic)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information (requires valid JWT token)"""
    return models.User_Pydantic.model_validate(current_user)


@router.post("/auth/users", response_model=models.User_Pydantic)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)"""
    # Check if username or email already exists
    existing_user = await models.User.filter(
        models.Q(username=request.username) | models.Q(email=request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create new user
    user = models.User(
        username=request.username,
        email=request.email,
        is_admin=request.is_admin
    )
    user.set_password(request.password)
    await user.save()
    
    return models.User_Pydantic.model_validate(user)


@router.get("/auth/users", response_model=List[models.User_Pydantic])
async def list_users(current_user: User = Depends(require_admin)):
    """List all users (admin only)"""
    users = await models.User.all()
    return [models.User_Pydantic.model_validate(user) for user in users]


@router.post("/auth/groups", response_model=models.Group_Pydantic)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_admin)
):
    """Create a new group (admin only)"""
    # Check if group name already exists
    existing_group = await models.Group.filter(name=request.name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists")
    
    # Create new group
    group = models.Group(
        name=request.name,
        description=request.description
    )
    await group.save()
    
    return models.Group_Pydantic.model_validate(group)


@router.get("/auth/groups", response_model=List[models.Group_Pydantic])
async def list_groups(current_user: User = Depends(require_admin)):
    """List all groups (admin only)"""
    groups = await models.Group.all()
    return [models.Group_Pydantic.model_validate(group) for group in groups]


@router.post("/auth/groups/{group_id}/members/{user_id}")
async def add_user_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin)
):
    """Add user to group (admin only)"""
    group = await models.Group.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = await models.User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await group.members.add(user)
    return {"message": f"User {user.username} added to group {group.name}"}


@router.delete("/auth/groups/{group_id}/members/{user_id}")
async def remove_user_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin)
):
    """Remove user from group (admin only)"""
    group = await models.Group.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = await models.User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await group.members.remove(user)
    return {"message": f"User {user.username} removed from group {group.name}"}


@router.put("/tree-items/{item_id}/permissions")
async def update_item_permissions(
    item_id: uuid.UUID,
    request: PermissionsUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update permissions on a tree item"""
    # Get the item
    item = await models.TreeItem.filter(id=str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    # Only admins or owners can change permissions
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not current_user.is_admin and item.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only admins or owners can change permissions")
    
    # Update fields if provided
    if request.owner_user_id is not None:
        if request.owner_user_id:
            # Verify user exists
            new_owner = await models.User.get_or_none(id=request.owner_user_id)
            if not new_owner:
                raise HTTPException(status_code=404, detail="Owner user not found")
        item.owner_user_id = request.owner_user_id
    
    if request.owner_group_id is not None:
        if request.owner_group_id:
            # Verify group exists
            new_group = await models.Group.get_or_none(id=request.owner_group_id)
            if not new_group:
                raise HTTPException(status_code=404, detail="Owner group not found")
        item.owner_group_id = request.owner_group_id
    
    if request.permissions is not None:
        # Validate permissions (should be valid octal, only use read/write bits)
        if request.permissions < 0 or request.permissions > 0o777:
            raise HTTPException(status_code=400, detail="Invalid permissions value")
        item.permissions = request.permissions
    
    await item.save()
    
    return {
        "message": "Permissions updated successfully",
        "permissions": item.get_permission_string(),
        "owner_user_id": item.owner_user_id,
        "owner_group_id": item.owner_group_id
    }
