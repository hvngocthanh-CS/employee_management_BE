from pydantic import BaseModel, Field, field_validator
from datetime import date as DateType
from datetime import time, datetime
from typing import Optional
from app.models.attendance import AttendanceStatus


class AttendanceBase(BaseModel):
    employee_id: int = Field(..., description="Employee ID")
    date: DateType = Field(..., description="Attendance date")
    check_in_time: Optional[time] = Field(None, description="Check-in time")
    check_out_time: Optional[time] = Field(None, description="Check-out time")
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT, description="Attendance status")


class AttendanceCreate(AttendanceBase):
    """Schema cho tạo mới Attendance"""
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        # Có thể chấm công cho quá khứ nhưng cảnh báo nếu quá xa
        from datetime import timedelta
        if v > DateType.today():
            raise ValueError('Không thể chấm công cho ngày trong tương lai')
        if v < DateType.today() - timedelta(days=30):
            raise ValueError('Không thể chấm công cho ngày quá 30 ngày trước')
        return v
    
    @field_validator('check_out_time')
    @classmethod
    def validate_checkout(cls, v, info):
        """Validate check_out_time > check_in_time"""
        check_in = info.data.get('check_in_time')
        if v and check_in and v <= check_in:
            raise ValueError('Giờ ra phải sau giờ vào')
        return v


class AttendanceUpdate(BaseModel):
    """Schema cho update Attendance"""
    employee_id: Optional[int] = None
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    status: Optional[AttendanceStatus] = None
    
    @field_validator('check_out_time')
    @classmethod
    def validate_checkout(cls, v, info):
        check_in = info.data.get('check_in_time')
        if v and check_in and v <= check_in:
            raise ValueError('Giờ ra phải sau giờ vào')
        return v


class AttendanceResponse(AttendanceBase):
    """Schema cho response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested data
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    
    # Calculated fields
    working_hours: Optional[float] = None  # Số giờ làm việc
    
    class Config:
        from_attributes = True


class AttendanceCheckIn(BaseModel):
    """Schema cho check-in nhanh"""
    employee_id: int
    check_in_time: Optional[time] = None  # None = thời gian hiện tại


class AttendanceCheckOut(BaseModel):
    """Schema cho check-out nhanh"""
    employee_id: int
    check_out_time: Optional[time] = None  # None = thời gian hiện tại


class AttendanceReport(BaseModel):
    """Schema cho báo cáo chấm công"""
    employee_id: int
    employee_name: str
    employee_code: str
    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    half_days: int
    working_hours: float
    attendances: list[AttendanceResponse]


class AttendanceSummary(BaseModel):
    """Schema cho tổng hợp chấm công theo ngày"""
    date: DateType
    total_employees: int
    present: int
    absent: int
    late: int
    half_day: int
    early_leave: int
