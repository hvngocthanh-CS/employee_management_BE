
from sqlalchemy import Column, Integer, Date, DateTime, Text, Enum, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class LeaveType(str, enum.Enum):
    """Leave type enum."""
    ANNUAL = "annual"
    SICK = "sick"
    UNPAID = "unpaid"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    EMERGENCY = "emergency"
    OTHER = "other"


class LeaveStatus(str, enum.Enum):
    """Leave status enum."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Leave(Base):
    """Leave model"""
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(
        Enum(LeaveType, name="leave_type"),
        nullable=False,
        index=True
    )
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(
        Enum(LeaveStatus, name="leave_status"),
        nullable=False,
        default=LeaveStatus.PENDING,
        index=True
    )
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    employee = relationship("Employee", back_populates="leaves")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_leaves")
    
    # Indexes for better query performance
    __table_args__ = (
        # Check constraint
        CheckConstraint('end_date >= start_date', name='check_leave_dates'),
        CheckConstraint('total_days > 0', name='check_positive_days'),
        
        Index('idx_leave_employee', 'employee_id'),
        Index('idx_leave_type', 'leave_type'),
        Index('idx_leave_status', 'status'),
        Index('idx_leave_start_date', 'start_date'),
        Index('idx_leave_end_date', 'end_date'),
        Index('idx_leave_approved_by', 'approved_by'),
        
        # Composite indexes for common queries
        Index('idx_leave_employee_status', 'employee_id', 'status'),
        Index('idx_leave_type_status', 'leave_type', 'status'),
        Index('idx_leave_date_range', 'start_date', 'end_date'),
    )
    
    def __repr__(self):
        return f"<Leave(id={self.id}, employee_id={self.employee_id}, type='{self.leave_type}', status='{self.status}')>"
