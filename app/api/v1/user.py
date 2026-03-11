from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import PermissionDependencies
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserCreateForEmployee,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserWithEmployee,
    UserChangePassword
)
from app.crud import user as crud_user

router = APIRouter()


@router.get("/", response_model=UserListResponse)
def list_users(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=10000),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(PermissionDependencies.can_read_user)
):
    """
    List all users
    Permissions: Admin only
    """
    users = crud_user.get_multi_with_employee(
        db,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active
    )
    
    # Count total
    count_query = db.query(User)
    if role:
        count_query = count_query.filter(User.role == role)
    if is_active is not None:
        count_query = count_query.filter(User.is_active == is_active)
    
    total = count_query.count()
    
    # Convert to response
    user_responses = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "employee_id": user.employee_id,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "employee_name": user.employee.full_name if user.employee else None,
            "employee_code": user.employee.employee_code if user.employee else None,
            "employee_email": user.employee.email if user.employee else None
        }
        user_responses.append(UserResponse(**user_dict))
    
    return UserListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        users=user_responses
    )


@router.get("/me", response_model=UserWithEmployee)
def get_current_user_info(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get thông tin user hiện tại"""
    user = crud_user.get_with_employee(db, id=current_user.id)
    
    result = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "employee_id": user.employee_id,
        "last_login": user.last_login,
        "created_at": user.created_at
    }
    
    if user.employee:
        result.update({
            "employee_name": user.employee.full_name,
            "employee_code": user.employee.employee_code,
            "employee_email": user.employee.email,
            "employee_full_name": user.employee.full_name,
            "employee_department": user.employee.department.name if user.employee.department else None,
            "employee_position": user.employee.position.title if user.employee.position else None
        })
    
    return UserWithEmployee(**result)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(PermissionDependencies.can_read_user)
):
    """
    Get user by ID
    Permissions: Admin only
    """
    user = crud_user.get_with_employee(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        **user.__dict__,
        employee_name=user.employee.full_name if user.employee else None,
        employee_code=user.employee.employee_code if user.employee else None,
        employee_email=user.employee.email if user.employee else None
    )


@router.post("/admin-manager", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_or_manager(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(PermissionDependencies.can_create_user)
):
    """
    Create new Admin or Manager user (no employee_id required).
    
    Permissions: Admin only
    
    Request Body:
      {
        "username": "new_manager",
        "password": "password123",
        "role": "admin" | "manager"
      }
    
    Note: Employee accounts should be created via /employees endpoint which auto-creates user.
    """
    from app.core.security import get_password_hash
    
    # Validate: cannot create employee via this endpoint
    if user_in.role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee accounts should be created via /api/v1/employees endpoint"
        )
    
    # Check if username exists
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' already exists"
        )
    
    # Create user
    new_user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        employee_id=None,  # Admin/Manager don't need employee_id
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        is_active=new_user.is_active,
        employee_id=None,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        employee_name=None,
        employee_code=None,
        employee_email=None
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreateForEmployee,
    current_user: User = Depends(PermissionDependencies.can_create_user)
):
    """
    Create new user for employees
    Permissions: Admin, Manager
    Must provide employee_id - used to create account for employee
    """
    try:
        user = crud_user.create(db, obj_in=user_in)
        
        return UserResponse(
            **user.__dict__,
            employee_name=user.employee.full_name if user.employee else None,
            employee_code=user.employee.employee_code if user.employee else None,
            employee_email=user.employee.email if user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Update user
    Permissions: Admin only
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Không cho phép admin tự deactivate chính mình
    if user_id == current_user.id and user_in.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Không cho phép chuyển sang Employee nếu user không có employee_id
    if user_in.role == UserRole.EMPLOYEE and user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change role to Employee - this user has no linked employee record. "
                   "Admin/Manager accounts created without employee_id cannot become Employee."
        )
    
    try:
        user = crud_user.update(db, db_obj=user, obj_in=user_in)
        
        return UserResponse(
            **user.__dict__,
            employee_name=user.employee.full_name if user.employee else None,
            employee_code=user.employee.employee_code if user.employee else None,
            employee_email=user.employee.email if user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/change-password", response_model=dict)
def change_password(
    *,
    db: Session = Depends(get_db),
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user)
):
    """Đổi password của chính mình"""
    try:
        crud_user.change_password(
            db,
            user=current_user,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{user_id}/reset-password", response_model=dict)
def reset_password(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    new_password: str = Query(..., min_length=6),
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Reset password for another user (admin function)
    Permissions: Admin only
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    crud_user.reset_password(db, user=user, new_password=new_password)
    return {"message": f"Password reset successfully for user {user.username}"}


@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Activate user account
    Permissions: Admin only
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = crud_user.activate(db, user=user)
    
    return UserResponse(
        **user.__dict__,
        employee_name=user.employee.full_name if user.employee else None,
        employee_code=user.employee.employee_code if user.employee else None,
        employee_email=user.employee.email if user.employee else None
    )


@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Deactivate user account
    Permissions: Admin only
    """
    # Không cho phép admin tự deactivate chính mình
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = crud_user.deactivate(db, user=user)
    
    return UserResponse(
        **user.__dict__,
        employee_name=user.employee.full_name if user.employee else None,
        employee_code=user.employee.employee_code if user.employee else None,
        employee_email=user.employee.email if user.employee else None
    )


@router.get("/role/{role}", response_model=List[UserResponse])
def get_users_by_role(
    *,
    db: Session = Depends(get_db),
    role: UserRole,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(PermissionDependencies.can_read_user)
):
    """
    Get users by role
    Permissions: Admin only
    """
    users = crud_user.get_users_by_role(
        db, role=role, skip=skip, limit=limit
    )
    
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "employee_id": user.employee_id,
            "last_login": user.last_login,
            "created_at": user.created_at
        }
        
        if user.employee:
            user_dict.update({
                "employee_name": user.employee.full_name,
                "employee_code": user.employee.employee_code,
                "employee_email": user.employee.email
            })
        
        result.append(UserResponse(**user_dict))
    
    return result


@router.get("/statistics/count-by-role", response_model=dict)
def get_user_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_user)
):
    """
    Get user count statistics by role
    Permissions: Admin only
    """
    stats = {}
    for role in UserRole:
        count = crud_user.count_by_role(db, role=role)
        stats[role.value] = count
    
    total_active = db.query(User).filter(User.is_active == True).count()
    total_inactive = db.query(User).filter(User.is_active == False).count()
    
    return {
        "by_role": stats,
        "total_active": total_active,
        "total_inactive": total_inactive,
        "total_users": total_active + total_inactive
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(PermissionDependencies.can_delete_user)
):
    """
    Delete user
    Permissions: Admin only
    """
    # Không cho phép admin tự xóa chính mình
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    crud_user.delete(db, id=user_id)
    return None