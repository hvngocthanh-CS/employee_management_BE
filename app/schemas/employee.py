from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.models.employee import Gender, EmploymentStatus


class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=50)
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hire_date: date
    employment_status: EmploymentStatus = Field(default=EmploymentStatus.ACTIVE)


class EmployeeCreate(EmployeeBase):
    employee_code: str = Field(..., min_length=1, max_length=20)
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_birth_date(cls, v):
        if v and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
    
    @field_validator('hire_date')
    @classmethod
    def validate_hire_date(cls, v):
        if v > date.today():
            raise ValueError("Start date cannot be in the future")
        return v

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hire_date: Optional[date] = None
    employment_status: Optional[EmploymentStatus] = None


class EmployeeResponse(EmployeeBase):
    id: int
    employee_code: str
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships (optional)
    department_name: Optional[str] = None
    position_title: Optional[str] = None
    
    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    employees: list[EmployeeResponse]