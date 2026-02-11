from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema cho User"""
    username: str = Field(..., min_length=3, max_length=50, description="Username duy nhất")
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="User role")
    is_active: bool = Field(default=True, description="Trạng thái active")


class UserCreate(BaseModel):
    """Schema cho tạo User mới - đơn giản cho WPF"""
    username: str = Field(..., min_length=3, max_length=50, description="Username duy nhất")
    password: str = Field(..., min_length=6, description="Password (tối thiểu 6 ký tự)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password phải có ít nhất 6 ký tự')
        return v


class UserCreateWithEmployee(UserBase):
    """Schema cho tạo User mới với employee_id"""
    employee_id: int = Field(..., description="ID nhân viên (phải tồn tại)")
    password: str = Field(..., min_length=6, description="Password (tối thiểu 6 ký tự)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password phải có ít nhất 6 ký tự')
        if v.isdigit():
            raise ValueError('Password không được chỉ toàn số')
        if v.isalpha():
            raise ValueError('Password nên có cả chữ và số')
        return v


class UserUpdate(BaseModel):
    """Schema cho update User - tất cả fields đều optional"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, description="Password mới")
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not v.isalnum() and '_' not in v:
                raise ValueError('Username chỉ được chứa chữ, số và dấu gạch dưới')
            return v.lower()
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 6:
                raise ValueError('Password phải có ít nhất 6 ký tự')
        return v


class UserChangePassword(BaseModel):
    """Schema cho đổi password"""
    old_password: str = Field(..., description="Password hiện tại")
    new_password: str = Field(..., min_length=6, description="Password mới")
    confirm_password: str = Field(..., description="Xác nhận password mới")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate password confirmation"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords không khớp')
        return v


class UserLogin(BaseModel):
    """Schema cho login"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    """Schema cho JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Schema cho data trong JWT token"""
    username: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    """Schema cho response - không trả về password"""
    id: int
    employee_id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    
    # Nested employee info (optional)
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    employee_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserWithEmployee(UserResponse):
    """Schema với đầy đủ thông tin employee"""
    employee_full_name: Optional[str] = None
    employee_department: Optional[str] = None
    employee_position: Optional[str] = None


class UserListResponse(BaseModel):
    """Schema cho list users với pagination"""
    total: int
    page: int
    page_size: int
    users: list[UserResponse]


class UserActivityLog(BaseModel):
    """Schema cho user activity log"""
    user_id: int
    username: str
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None