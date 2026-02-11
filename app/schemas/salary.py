from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime, date


class SalaryBase(BaseModel):
    employee_id: int = Field(..., description="Employee ID")
    base_salary: Decimal = Field(..., gt=0, decimal_places=2, description="Base salary (VND)")
    effective_from: date = Field(..., description="Effective from date")
    effective_to: Optional[date] = Field(None, description="Effective to date")


class SalaryCreate(SalaryBase):
    
    @field_validator('base_salary')
    @classmethod
    def validate_salary(cls, v):
        if v <= 0:
            raise ValueError('Lương phải lớn hơn 0')
        if v > Decimal('999999999999.99'):
            raise ValueError('Lương vượt quá giới hạn cho phép')
        return v
    
    @field_validator('effective_to')
    @classmethod
    def validate_effective_dates(cls, v, info):
        """Validate effective_to >= effective_from"""
        effective_from = info.data.get('effective_from')
        if v and effective_from and v < effective_from:
            raise ValueError('Ngày kết thúc phải >= ngày bắt đầu')
        return v

class SalaryUpdate(BaseModel):
    employee_id: Optional[int] = None
    base_salary: Optional[Decimal] = Field(default=None, gt=0)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    
    @field_validator('base_salary')
    @classmethod
    def validate_salary(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Lương phải lớn hơn 0')
        return v


class SalaryResponse(SalaryBase):
    """Schema cho response"""
    id: int
    created_at: datetime
    
    # Nested data
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    
    class Config:
        from_attributes = True


class SalaryHistory(BaseModel):
    """Schema cho lịch sử lương của nhân viên"""
    employee_id: int
    employee_name: str
    employee_code: str
    salaries: list[SalaryResponse]
    current_salary: Optional[Decimal] = None

class SalaryStatistics(BaseModel):
    """Schema cho thống kê lương"""
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    average_salary: Decimal
    min_salary: Decimal
    max_salary: Decimal
    total_employees: int