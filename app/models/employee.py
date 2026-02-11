from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class Gender(str, enum.Enum):
    """Gender enum."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EmploymentStatus(str, enum.Enum):
    """Employment status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Employee(Base):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, nullable=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    full_name = Column(String(100), nullable=True, index=True)
    email = Column(String(100), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    date_of_birth = Column(Date, nullable=True, index=True)
    
    # Sử dụng Enum generic thay vì PG_ENUM
    gender = Column(Enum(Gender, name="gender_enum"), nullable=True)
    
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True, index=True)
    hire_date = Column(Date, nullable=True, index=True)
    
    employment_status = Column(
        Enum(EmploymentStatus, name="employment_status_enum"),
        nullable=False,
        default=EmploymentStatus.ACTIVE,
        index=True
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False)
    salaries = relationship("Salary", back_populates="employee", lazy='dynamic')
    attendances = relationship("Attendance", back_populates="employee", lazy='dynamic')
    leaves = relationship("Leave", back_populates="employee", lazy='dynamic')
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_employee_dept_status', 'department_id', 'employment_status'),
        Index('idx_employee_position_status', 'position_id', 'employment_status'),
    )
    
    def __repr__(self):
        return f"<Employee(id={self.id}, code='{self.employee_code}', name='{self.full_name}')>"
