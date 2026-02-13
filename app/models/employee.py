"""
Employee Model
==============
Represents an employee in the organization.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    """Employee SQLAlchemy model"""
    __tablename__ = "employees"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal Info
    full_name = Column(String(100), nullable=False, index=True)
    employee_code = Column(String(20), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    
    # Foreign Keys
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    position_id = Column(
        Integer,
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False)
    salaries = relationship("Salary", back_populates="employee", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_employee_full_name', 'full_name'),
        Index('idx_employee_code', 'employee_code'),
        Index('idx_employee_email', 'email'),
        Index('idx_employee_department', 'department_id'),
        Index('idx_employee_position', 'position_id'),
    )
    
    def __repr__(self):
        return f"<Employee(id={self.id}, code='{self.employee_code}', name='{self.full_name}')>"
