"""
Department Schemas
==================
Pydantic models for request/response validation.

Demonstrates:
  - DepartmentCreate: for POST requests (user input)
  - DepartmentUpdate: for PUT requests (partial updates)
  - DepartmentResponse: for GET responses (database output)
"""

from pydantic import BaseModel, Field
from typing import Optional


class DepartmentCreate(BaseModel):
    """
    Schema for creating a new department.
    Users provide: just the name
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Department name (must be unique)"
    )


class DepartmentUpdate(BaseModel):
    """
    Schema for updating a department.
    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Department name"
    )


class DepartmentResponse(BaseModel):
    """
    Schema for returning department data from the API.
    Includes the ID and all fields stored in the database.
    from_attributes=True tells Pydantic to work with SQLAlchemy objects.
    """
    id: int
    name: str
    
    class Config:
        from_attributes = True  # Works with SQLAlchemy ORM objects
