from pydantic import BaseModel, Field, field_validator, ConfigDict, model_serializer
from decimal import Decimal
from typing import Optional, Any
from datetime import datetime, date


class SalaryBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )
    
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
    username: Optional[str] = None
    role: Optional[str] = None
    
    # Additional fields for frontend compatibility
    amount: Optional[Decimal] = None  # Alias for base_salary
    currency: str = "VND"
    notes: str = ""
    
    model_config = ConfigDict(from_attributes=True)
        
    def model_post_init(self, __context) -> None:
        """Set amount to base_salary after initialization"""
        if self.amount is None and self.base_salary:
            self.amount = self.base_salary
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to convert Decimal to float for JSON"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'base_salary': float(self.base_salary) if self.base_salary else None,
            'amount': float(self.amount) if self.amount else None,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'employee_name': self.employee_name,
            'employee_code': self.employee_code,
            'username': self.username,
            'role': self.role,
            'currency': self.currency,
            'notes': self.notes,
        }


class SalaryHistory(BaseModel):
    """Schema cho lịch sử lương của nhân viên"""
    model_config = ConfigDict(from_attributes=True)
    
    employee_id: int
    employee_name: str
    employee_code: str
    salaries: list[SalaryResponse]
    current_salary: Optional[Decimal] = None
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to convert Decimal to float"""
        return {
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'employee_code': self.employee_code,
            'salaries': [s.model_dump() if hasattr(s, 'model_dump') else s for s in self.salaries],
            'current_salary': float(self.current_salary) if self.current_salary else None,
        }

class SalaryStatistics(BaseModel):
    """Schema cho thống kê lương"""
    model_config = ConfigDict(from_attributes=True)
    
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    average_salary: Decimal
    min_salary: Decimal
    max_salary: Decimal
    total_employees: int
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to convert Decimal to float"""
        return {
            'department_id': self.department_id,
            'department_name': self.department_name,
            'average_salary': float(self.average_salary) if self.average_salary else None,
            'min_salary': float(self.min_salary) if self.min_salary else None,
            'max_salary': float(self.max_salary) if self.max_salary else None,
            'total_employees': self.total_employees,
        }