from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, Token, UserProfile
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.permissions import get_user_permissions, get_menu_permissions

router = APIRouter()


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Login với username và password - return JWT token với user info
    """
    # Kiểm tra username trong DB
    user = db.query(User).filter(User.username == user_in.username).first()
    
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
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Get user permissions and menu visibility
    permissions = get_user_permissions(user)
    menu_permissions = get_menu_permissions(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
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
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user
    """
    # Kiểm tra username đã tồn tại?
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Tạo user mới với password hashed
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "username": new_user.username,
        "id": new_user.id
    }

