from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Authorization
    role = Column(
        Enum(UserRole, name='user_role_enum'),
        default=UserRole.EMPLOYEE,
        nullable=False,
        index=True
    )
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
    approved_leaves = relationship(
        "Leave",
        foreign_keys="Leave.approved_by",
        back_populates="approver",
        lazy='dynamic'
    )
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_employee', 'employee_id'),
        # Composite index for common queries
        Index('idx_user_role_active', 'role', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
