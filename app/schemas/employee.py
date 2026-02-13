"""
Employee Schemas
================
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee."""
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Employee full name"
    )
    employee_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Employee code (must be unique)"
    )
    email: EmailStr = Field(
        ...,
        description="Employee email (must be unique)"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Employee phone number"
    )
    department_id: Optional[int] = Field(
        None,
        description="Department ID (foreign key)"
    )
    position_id: Optional[int] = Field(
        None,
        description="Position ID (foreign key)"
    )


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Employee full name"
    )
    employee_code: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Employee code"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Employee email"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Employee phone number"
    )
    department_id: Optional[int] = Field(
        None,
        description="Department ID"
    )
    position_id: Optional[int] = Field(
        None,
        description="Position ID"
    )


class EmployeeResponse(BaseModel):
    """Schema for returning employee data from the API."""
    id: int
    full_name: str
    employee_code: str
    email: str
    phone: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    
    # Related data (optional)
    department_name: Optional[str] = None
    position_title: Optional[str] = None
    
    class Config:
        from_attributes = True
