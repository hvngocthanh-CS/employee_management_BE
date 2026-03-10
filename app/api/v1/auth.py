from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, Token, UserProfile,
    ChangePasswordRequest, ResetPasswordRequest, RefreshTokenRequest
)
from app.models.user import User, UserRole
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, hash_refresh_token, refresh_token_expires_at
)
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.permissions import get_user_permissions, get_menu_permissions, PermissionDependencies

router = APIRouter()


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Login bằng username cho tất cả roles (Admin, Manager, Employee)
    """
    identifier = user_in.identifier.strip()
    
    # Tất cả user đều login bằng username
    user = db.query(User).filter(User.username == identifier).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # --- Issue access token (JWT, short-lived) ---
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # --- Issue refresh token (opaque random, long-lived) ---
    raw_refresh_token = create_refresh_token()
    user.refresh_token_hash = hash_refresh_token(raw_refresh_token)
    user.refresh_token_expires_at = refresh_token_expires_at()

    # Update last_login timestamp
    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Get user permissions and menu visibility
    permissions = get_user_permissions(user)
    menu_permissions = get_menu_permissions(user)

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "employee_id": user.employee_id,
            "is_active": user.is_active,
            "permissions": permissions,
            "menu_permissions": menu_permissions
        }
    }


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile với permissions
    """
    # Get user permissions and menu visibility
    permissions = get_user_permissions(current_user)
    menu_permissions = get_menu_permissions(current_user)
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        employee_id=current_user.employee_id,
        is_active=current_user.is_active,
        permissions=permissions,
        menu_permissions=menu_permissions,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/register")
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_create_user)
):
    """
    Create new user account (Admin only).
    
    This endpoint is PROTECTED - only authenticated Admin can create new users.
    - Admin can create: Admin, Manager, or Employee accounts
    - For Employee accounts, use /api/v1/employees/ which auto-creates user account
    
    Permissions: Admin only
    """
    from app.core.security import get_password_hash
    
    # Kiểm tra username đã tồn tại?
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Tạo user mới với password hashed và role (không có employee_id)
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        hashed_password=hashed_password,
        role=user_in.role,
        employee_id=None,  # Admin/Manager không cần employee_id
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Account registered successfully",
        "username": new_user.username,
        "role": new_user.role.value,
        "id": new_user.id
    }


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change password for current user (employee can change their own password).
    
    Permissions: All authenticated users
    
    Request Body:
      {
        "current_password": "old_password123",
        "new_password": "new_password456"
      }
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {
        "message": "Password changed successfully"
    }


@router.post("/reset-password")
def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Reset password for any user (Admin only).
    
    Permissions: Admin only
    
    Request Body:
      {
        "user_id": 5,
        "new_password": "reset_password123"
      }
      
    Use case: When employee forgets password or admin wants to reset it.
    """
    # Find the target user
    target_user = db.query(User).filter(User.id == reset_data.user_id).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {reset_data.user_id} not found"
        )
    
    # Update password
    target_user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()
    
    return {
        "message": f"Password reset successfully for user: {target_user.username}",
        "user_id": target_user.id,
        "username": target_user.username
    }


@router.post("/refresh", response_model=Token)
def refresh_tokens(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh Access Token bằng Refresh Token.

    Flow (Token Rotation):
      1. Client gửi refresh_token cũ.
      2. Server hash nó, tìm user có hash khớp và kiểm tra chưa hết hạn.
      3. Nếu hợp lệ: cấp một cặp token MỚI, ghi đè hash cũ trong DB (invalidate cái cũ).
      4. Nếu không hợp lệ: trả 401 — có thể token bị đánh cắp.

    Tại sao dùng Token Rotation?
      - Nếu kẻ tấn công lấy được refresh token và dùng trước legitimate user:
        legitimate user gửi token cũ → server phát hiện bất thường → có thể thu hồi toàn bộ session.
    """
    from datetime import datetime, timezone

    incoming_hash = hash_refresh_token(body.refresh_token)

    # Find user by refresh token hash
    user = db.query(User).filter(User.refresh_token_hash == incoming_hash).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check expiration
    if user.refresh_token_expires_at is None or \
            user.refresh_token_expires_at < datetime.now(timezone.utc):
        # Token expired — clear it and force re-login
        user.refresh_token_hash = None
        user.refresh_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired, please login again",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # --- Token Rotation: issue NEW pair, invalidate old refresh token ---
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    new_raw_refresh = create_refresh_token()
    user.refresh_token_hash = hash_refresh_token(new_raw_refresh)
    user.refresh_token_expires_at = refresh_token_expires_at()
    db.commit()

    permissions = get_user_permissions(user)
    menu_permissions = get_menu_permissions(user)

    return {
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "employee_id": user.employee_id,
            "is_active": user.is_active,
            "permissions": permissions,
            "menu_permissions": menu_permissions
        }
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout: vô hiệu hóa refresh token hiện tại của user.

    - Access token vẫn còn hiệu lực cho đến khi hết hạn (30 phút) — đây là đặc điểm của JWT stateless.
    - Refresh token bị xóa trong DB ngay lập tức → không thể lấy access token mới nữa.
    - Best practice: frontend cũng phải xóa access token khỏi bộ nhớ sau khi gọi API này.
    """
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires_at = None
    db.commit()
