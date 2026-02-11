from typing import List, Optional
from datetime import date, time, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_manager_or_admin
from app.models.user import User
from app.models.attendance import AttendanceStatus
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceReport,
    AttendanceSummary
)
from app.crud import attendance as crud_attendance, employee as crud_employee

router = APIRouter()


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    *,
    db: Session = Depends(get_db),
    check_in_data: AttendanceCheckIn,
    current_user: User = Depends(get_current_user)
):
    """
    Check-in cho nhân viên
    Thời gian mặc định là hiện tại
    """
    try:
        attendance = crud_attendance.attendance.check_in(
            db,
            employee_id=check_in_data.employee_id,
            check_in_time=check_in_data.check_in_time
        )
        
        employee = crud_employee.employee.get(db, id=check_in_data.employee_id)
        
        return AttendanceResponse(
            **attendance.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    *,
    db: Session = Depends(get_db),
    check_out_data: AttendanceCheckOut,
    current_user: User = Depends(get_current_user)
):
    """
    Check-out cho nhân viên
    Thời gian mặc định là hiện tại
    """
    try:
        attendance = crud_attendance.attendance.check_out(
            db,
            employee_id=check_out_data.employee_id,
            check_out_time=check_out_data.check_out_time
        )
        
        employee = crud_employee.employee.get(db, id=check_out_data.employee_id)
        
        # Calculate working hours
        working_hours = None
        if attendance.check_in_time and attendance.check_out_time:
            check_in = datetime.combine(date.today(), attendance.check_in_time)
            check_out_dt = datetime.combine(date.today(), attendance.check_out_time)
            working_hours = (check_out_dt - check_in).total_seconds() / 3600
        
        return AttendanceResponse(
            **attendance.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None,
            working_hours=working_hours
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/employee/{employee_id}", response_model=List[AttendanceResponse])
def get_employee_attendances(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user)
):
    """Get attendance records của một nhân viên"""
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    attendances = crud_attendance.attendance.get_by_employee(
        db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    result = []
    for att in attendances:
        # Calculate working hours
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600
        
        result.append(
            AttendanceResponse(
                **att.__dict__,
                employee_name=employee.full_name,
                employee_code=employee.employee_code,
                department_name=employee.department.name if employee.department else None,
                working_hours=working_hours
            )
        )
    
    return result


@router.get("/date/{attendance_date}", response_model=List[AttendanceResponse])
def get_attendances_by_date(
    *,
    db: Session = Depends(get_db),
    attendance_date: date,
    department_id: Optional[int] = None,
    status: Optional[AttendanceStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Get tất cả attendance trong một ngày"""
    attendances = crud_attendance.attendance.get_by_date(
        db,
        attendance_date=attendance_date,
        department_id=department_id,
        status=status
    )
    
    result = []
    for att in attendances:
        employee = crud_employee.employee.get(db, id=att.employee_id)
        
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600
        
        result.append(
            AttendanceResponse(
                **att.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None,
                working_hours=working_hours
            )
        )
    
    return result


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_in: AttendanceCreate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Tạo attendance record thủ công
    Yêu cầu role MANAGER hoặc ADMIN
    """
    # Check employee exists
    employee = crud_employee.employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check if already exists
    existing = crud_attendance.attendance.get_by_employee_and_date(
        db,
        employee_id=attendance_in.employee_id,
        attendance_date=attendance_in.date
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance record already exists for {attendance_in.date}"
        )
    
    attendance = crud_attendance.attendance.create(db, obj_in=attendance_in)
    
    working_hours = None
    if attendance.check_in_time and attendance.check_out_time:
        check_in = datetime.combine(date.today(), attendance.check_in_time)
        check_out = datetime.combine(date.today(), attendance.check_out_time)
        working_hours = (check_out - check_in).total_seconds() / 3600
    
    return AttendanceResponse(
        **attendance.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        department_name=employee.department.name if employee.department else None,
        working_hours=working_hours
    )


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_id: int,
    attendance_in: AttendanceUpdate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Update attendance record
    Yêu cầu role MANAGER hoặc ADMIN
    """
    attendance = crud_attendance.attendance.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    attendance = crud_attendance.attendance.update(
        db, db_obj=attendance, obj_in=attendance_in
    )
    
    employee = crud_employee.employee.get(db, id=attendance.employee_id)
    
    working_hours = None
    if attendance.check_in_time and attendance.check_out_time:
        check_in = datetime.combine(date.today(), attendance.check_in_time)
        check_out = datetime.combine(date.today(), attendance.check_out_time)
        working_hours = (check_out - check_in).total_seconds() / 3600
    
    return AttendanceResponse(
        **attendance.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department.name if employee and employee.department else None,
        working_hours=working_hours
    )


@router.get("/report/monthly/{employee_id}", response_model=AttendanceReport)
def get_monthly_report(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    current_user: User = Depends(get_current_user)
):
    """Báo cáo chấm công theo tháng"""
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    report = crud_attendance.attendance.get_monthly_report(
        db, employee_id=employee_id, month=month, year=year
    )
    
    # Convert attendances to response format
    attendance_responses = []
    for att in report["attendances"]:
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600
        
        attendance_responses.append(
            AttendanceResponse(
                **att.__dict__,
                employee_name=employee.full_name,
                employee_code=employee.employee_code,
                working_hours=working_hours
            )
        )
    
    return AttendanceReport(
        employee_id=employee_id,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        month=month,
        year=year,
        total_days=report["total_days"],
        present_days=report["present_days"],
        absent_days=report["absent_days"],
        late_days=report["late_days"],
        half_days=report["half_days"],
        working_hours=report["working_hours"],
        attendances=attendance_responses
    )


@router.get("/summary/daily", response_model=AttendanceSummary)
def get_daily_summary(
    *,
    db: Session = Depends(get_db),
    attendance_date: date = Query(default_factory=date.today),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Tổng hợp chấm công theo ngày"""
    summary = crud_attendance.attendance.get_daily_summary(
        db, attendance_date=attendance_date, department_id=department_id
    )
    
    return AttendanceSummary(**summary)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Delete attendance record
    Yêu cầu role MANAGER hoặc ADMIN
    """
    attendance = crud_attendance.attendance.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    crud_attendance.attendance.delete(db, id=attendance_id)
    return None