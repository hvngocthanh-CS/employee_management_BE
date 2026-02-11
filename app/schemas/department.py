from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    code: str = Field(..., min_length=1, max_length=20, description="Department code")
    description: Optional[str] = Field(None, description="Department description")

# Schema cho Create (không cần id, timestamps)
class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None

# Schema cho Response (đầy đủ thông tin từ database)
class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema với thống kê (count employees)
class DepartmentWithStats(DepartmentResponse):
    employee_count: int = 0
