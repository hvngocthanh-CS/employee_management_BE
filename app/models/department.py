"""
Department Model
================
Represents a department in the organization.
Demonstrates:
  - Basic SQLAlchemy model structure
  - One-to-Many relationship (one dept has many employees)
  - Indexes for frequently queried fields
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    """
    Department SQLAlchemy model
    
    This table stores department information. Employees belong to departments.
    """
    __tablename__ = "departments"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Columns - name must be unique (each department has a distinct name)
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Relationships
    # Tells SQLAlchemy: Department has many Employees
    # back_populates="department" creates the reverse relationship
    # lazy='selectin' loads employees efficiently when we access dept.employees
    employees = relationship(
        "Employee",
        back_populates="department",
        lazy="selectin",
        cascade="all, delete-orphan"  # Delete employees when dept is deleted
    )
    
    def __repr__(self):
        """String representation for debugging"""
        return f"<Department(id={self.id}, name='{self.name}')>"
