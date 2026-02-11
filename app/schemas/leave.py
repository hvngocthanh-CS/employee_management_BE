from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.models.leave import LeaveType, LeaveStatus


class LeaveBase(BaseModel):
    employee_id: int = Field(..., description="Employee ID")
    leave_type: LeaveType = Field(..., description="Leave type")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    total_days: int = Field(..., gt=0, description="Total number of leave days")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for leave")
    

class LeaveCreate(LeaveBase):
    """Schema cho tạo đơn nghỉ phép"""
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        """Start date không được quá xa trong quá khứ"""
        from datetime import timedelta
        if v < date.today() - timedelta(days=7):
            raise ValueError('Ngày bắt đầu không được quá 7 ngày trong quá khứ')
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """End date phải >= start date"""
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('Ngày kết thúc phải >= ngày bắt đầu')
        return v
    
    @field_validator('total_days')
    @classmethod
    def validate_total_days(cls, v, info):
        """Validate total_days phù hợp với khoảng thời gian"""
        start_date = info.data.get('start_date')
        end_date = info.data.get('end_date')
        
        if start_date and end_date:
            calculated_days = (end_date - start_date).days + 1
            if v > calculated_days:
                raise ValueError(f'Số ngày nghỉ ({v}) không được lớn hơn khoảng thời gian ({calculated_days} ngày)')
            if v > 365:
                raise ValueError('Số ngày nghỉ không được vượt quá 365 ngày')
        
        return v


class LeaveUpdate(BaseModel):
    employee_id: Optional[int] = None
    leave_type: Optional[LeaveType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_days: Optional[int] = Field(None, gt=0)
    reason: Optional[str] = Field(None, max_length=500)
    status: Optional[LeaveStatus] = None


class LeaveApproval(BaseModel):
    status: LeaveStatus = Field(..., description="Approval status: approved or rejected")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in [LeaveStatus.APPROVED, LeaveStatus.REJECTED]:
            raise ValueError('Status phải là APPROVED hoặc REJECTED')
        return v

class LeaveCancel(BaseModel):
    """Schema cho hủy đơn nghỉ phép"""
    reason: Optional[str] = Field(None, max_length=500, description="Lý do hủy")


class LeaveResponse(LeaveBase):
    """Schema cho response"""
    id: int
    status: LeaveStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested data
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class LeaveListResponse(BaseModel):
    """Schema cho list với pagination"""
    total: int
    page: int
    page_size: int
    leaves: list[LeaveResponse]


class LeaveBalance(BaseModel):
    """Schema cho số ngày phép còn lại"""
    employee_id: int
    employee_name: str
    year: int
    total_annual_leave: int = Field(default=12, description="Tổng số ngày phép năm")
    used_annual_leave: int = Field(default=0, description="Đã sử dụng")
    remaining_annual_leave: int = Field(default=12, description="Còn lại")
    pending_leave: int = Field(default=0, description="Đang chờ duyệt")


class LeaveStatistics(BaseModel):
    """Schema cho thống kê nghỉ phép"""
    month: int
    year: int
    total_leaves: int
    by_type: dict[str, int]  # {LeaveType: count}
    by_status: dict[str, int]  # {LeaveStatus: count}
    by_department: dict[str, int]  # {department_name: count}


class LeaveCalendar(BaseModel):
    """Schema cho lịch nghỉ phép"""
    date: date
    leaves: list[LeaveResponse]
    total_on_leave: int
