from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema cho User"""
    username: str = Field(..., min_length=3, max_length=50, description="Username duy nhất")
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="User role")
    is_active: bool = Field(default=True, description="Trạng thái active")


class UserCreate(BaseModel):
    """Schema cho admin/manager tự đăng ký - không cần employee_id"""
    username: str = Field(..., min_length=3, max_length=50, description="Username duy nhất")
    password: str = Field(..., min_length=6, description="Password (tối thiểu 6 ký tự)")
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="User role")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password phải có ít nhất 6 ký tự')
        return v


class UserCreateForEmployee(BaseModel):
    """Schema cho admin/manager tạo tài khoản cho employee - cần employee_id"""
    employee_id: int = Field(..., description="ID nhân viên (phải tồn tại)")
    username: str = Field(..., min_length=3, max_length=50, description="Username duy nhất")
    password: str = Field(..., min_length=6, description="Password (tối thiểu 6 ký tự)")
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="User role")
    
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
    """Schema cho login - hỗ trợ cả email (employee) và username (admin/manager)"""
    identifier: str = Field(..., description="Email (for employees) or Username (for admin/manager)")
    password: str = Field(..., description="Password")


class ChangePasswordRequest(BaseModel):
    """Schema cho đổi password của chính mình"""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters')
        return v


class ResetPasswordRequest(BaseModel):
    """Schema cho admin/manager reset password của employee"""
    user_id: int = Field(..., description="User ID to reset password")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters')
        return v


class UserProfile(BaseModel):
    """Schema cho user profile với permissions"""
    id: int
    username: str
    role: str
    employee_id: Optional[int] = None
    is_active: bool
    permissions: List[str] = []
    menu_permissions: Dict[str, Any] = {}
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInToken(BaseModel):
    """Schema cho user data trong token response"""
    id: int
    username: str
    role: str
    employee_id: Optional[int] = None
    is_active: bool
    permissions: List[str] = []
    menu_permissions: Dict[str, Any] = {}


class Token(BaseModel):
    """Schema cho JWT token response với user info"""
    access_token: str = Field(..., description="JWT access token (short-lived, 30 min)")
    refresh_token: str = Field(..., description="Opaque refresh token (long-lived, 7 days)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Access token expiration time in seconds")
    user: Optional[UserInToken] = None  # Include user info in login response


class RefreshTokenRequest(BaseModel):
    """Schema cho yêu cầu làm mới access token"""
    refresh_token: str = Field(..., description="Refresh token nhận được lúc login")


class TokenData(BaseModel):
    """Schema cho data trong JWT token"""
    username: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    """Schema cho response - không trả về password, không validate min_length"""
    id: int
    username: str
    role: UserRole
    is_active: bool = True
    employee_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
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