from sqlalchemy import Column, Integer, Date, Time, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AttendanceStatus(str, enum.Enum):
    """Attendance status enum."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    EARLY_LEAVE = "early_leave"


class Attendance(Base):
    """Attendance model"""
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(Time, nullable=True)
    check_out_time = Column(Time, nullable=True)
    status = Column(
        Enum(AttendanceStatus, name="attendance_status"),
        nullable=False,
        default=AttendanceStatus.PRESENT,
        index=True
    )
    
    # Relationships
    employee = relationship("Employee", back_populates="attendances")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
        Index('idx_attendance_employee', 'employee_id'),
        Index('idx_attendance_date', 'date'),
        Index('idx_attendance_status', 'status'),
        # Composite indexes for common queries
        Index('idx_attendance_employee_date', 'employee_id', 'date'),
        Index('idx_attendance_date_status', 'date', 'status'),
        Index('idx_attendance_employee_status', 'employee_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, employee_id={self.employee_id}, date='{self.date}', status='{self.status}')>"
