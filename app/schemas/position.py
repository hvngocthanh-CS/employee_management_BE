from pydantic import BaseModel, Field
from typing import Optional
from app.models.position import PositionLevel


class PositionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Position title")
    code: str = Field(..., min_length=1, max_length=20, description="Position code")
    level: PositionLevel = Field(..., description="Position level")
    description: Optional[str] = Field(None, description="Position description")


class PositionCreate(PositionBase):
    """Schema cho tạo mới Position"""
    pass


class PositionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    level: Optional[PositionLevel] = None
    description: Optional[str] = None


class PositionResponse(PositionBase):
    """Schema cho response từ database"""
    id: int

    class Config:
        from_attributes = True


class PositionWithStats(PositionResponse):
    """Schema với thống kê số lượng nhân viên"""
    employee_count: int = 0
    active_employee_count: int = 0
