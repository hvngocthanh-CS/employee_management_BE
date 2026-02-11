from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate
from app.models.user import User

router = APIRouter()


@router.post("/login")
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Login với username và password
    """
    # Kiểm tra username trong DB
    user = db.query(User).filter(User.username == user_in.username).first()
    
    if not user or user.hashed_password != user_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return {
        "message": "Login successful",
        "username": user.username,
        "id": user.id
    }


@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user - đơn giản cho WPF
    """
    # Kiểm tra username đã tồn tại?
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Tạo user mới (không cần employee_id)
    new_user = User(
        username=user_in.username,
        hashed_password=user_in.password,
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
