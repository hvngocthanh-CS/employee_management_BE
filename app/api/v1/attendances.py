from typing import List, Optional
from datetime import date, time, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import PermissionDependencies, check_resource_ownership
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
from app.models.employee import Employee as EmployeeModel
from app.models.department import Department as DepartmentModel

router = APIRouter()


@router.get("/", response_model=List[AttendanceResponse])
def list_all_attendances(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(PermissionDependencies.can_read_attendance)
):
    """
    List all attendance records (Admin/Manager only)
    Permissions: Admin, Manager
    
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      employee_id: Filter by specific employee (optional)
      start_date: Filter from this date (optional)
      end_date: Filter to this date (optional)
    """
    # Admin/Manager can view all attendances
    from app.models.attendance import Attendance
    query = db.query(Attendance).options(
        joinedload(Attendance.employee).joinedload(EmployeeModel.department)
    )

    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    attendances = query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()

    result = []
    for att in attendances:
        emp = att.employee
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600

        result.append(
            AttendanceResponse(
                **att.__dict__,
                attendance_date=att.date,
                employee_name=emp.full_name if emp else None,
                employee_code=emp.employee_code if emp else None,
                department_name=emp.department.name if emp and emp.department else None,
                working_hours=working_hours
            )
        )

    return result


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_in: AttendanceCreate,
    current_user: User = Depends(PermissionDependencies.can_create_attendance)
):
    """
    Create attendance record manually
    Permissions: Admin, Manager
    """
    employee = crud_employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check if attendance already exists for this date
    from app.models.attendance import Attendance
    existing = db.query(Attendance).filter(
        Attendance.employee_id == attendance_in.employee_id,
        Attendance.date == attendance_in.date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists for this date"
        )
    
    attendance = crud_attendance.create(db, obj_in=attendance_in)
    
    working_hours = None
    if attendance.check_in_time and attendance.check_out_time:
        check_in = datetime.combine(date.today(), attendance.check_in_time)
        check_out = datetime.combine(date.today(), attendance.check_out_time)
        working_hours = (check_out - check_in).total_seconds() / 3600
    
    return AttendanceResponse(
        **attendance.__dict__,
        attendance_date=attendance.date,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        department_name=employee.department.name if employee.department else None,
        working_hours=working_hours
    )


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    *,
    db: Session = Depends(get_db),
    check_in_data: AttendanceCheckIn,
    current_user: User = Depends(PermissionDependencies.can_mark_own_attendance)
):
    """
    Check-in cho nhân viên
    Thời gian mặc định là hiện tại
    Employee chỉ có thể check-in cho chính mình
    """
    # Employee chỉ có thể check-in cho chính mình
    if not check_resource_ownership(current_user, check_in_data.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check-in for yourself"
        )
    
    # Convert datetime to time if needed
    check_in_time = None
    if check_in_data.check_in_time:
        if isinstance(check_in_data.check_in_time, datetime):
            check_in_time = check_in_data.check_in_time.time()
        else:
            check_in_time = check_in_data.check_in_time
    
    try:
        attendance = crud_attendance.check_in(
            db,
            employee_id=check_in_data.employee_id,
            check_in_time=check_in_time
        )
        
        employee = crud_employee.get(db, id=check_in_data.employee_id)
        
        return AttendanceResponse(
            **attendance.__dict__,
            attendance_date=attendance.date,
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
    current_user: User = Depends(PermissionDependencies.can_mark_own_attendance)
):
    """
    Check-out cho nhân viên
    Thời gian mặc định là hiện tại
    Employee chỉ có thể check-out cho chính mình
    """
    # Employee chỉ có thể check-out cho chính mình
    if not check_resource_ownership(current_user, check_out_data.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check-out for yourself"
        )
    
    # Convert datetime to time if needed
    check_out_time = None
    if check_out_data.check_out_time:
        if isinstance(check_out_data.check_out_time, datetime):
            check_out_time = check_out_data.check_out_time.time()
        else:
            check_out_time = check_out_data.check_out_time
    
    try:
        attendance = crud_attendance.check_out(
            db,
            employee_id=check_out_data.employee_id,
            check_out_time=check_out_time
        )
        
        employee = crud_employee.get(db, id=check_out_data.employee_id)
        
        # Calculate working hours
        working_hours = None
        if attendance.check_in_time and attendance.check_out_time:
            check_in = datetime.combine(date.today(), attendance.check_in_time)
            check_out_dt = datetime.combine(date.today(), attendance.check_out_time)
            working_hours = (check_out_dt - check_in).total_seconds() / 3600
        
        return AttendanceResponse(
            **attendance.__dict__,
            attendance_date=attendance.date,
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
    current_user: User = Depends(PermissionDependencies.can_read_own_attendance)
):
    """
    Get attendance records của một nhân viên
    Employee chỉ có thể xem attendance của mình
    Admin/Manager có thể xem tất cả
    """
    # Check permissions
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own attendance records"
        )
    
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    attendances = crud_attendance.get_by_employee(
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
                attendance_date=att.date,
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
    attendances = crud_attendance.get_by_date(
        db,
        attendance_date=attendance_date,
        department_id=department_id,
        status=status
    )
    
    result = []
    for att in attendances:
        employee = crud_employee.get(db, id=att.employee_id)
        
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600
        
        result.append(
            AttendanceResponse(
                **att.__dict__,
                attendance_date=att.date,
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
    current_user: User = Depends(PermissionDependencies.can_create_attendance)
):
    """
    Create attendance record manually
    Permissions: Admin, Manager
    """
    # Check employee exists
    employee = crud_employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Validate: attendance date must be >= employee hire_date
    if employee.hire_date and attendance_in.date < employee.hire_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ngày chấm công ({attendance_in.date}) phải >= ngày thuê nhân viên ({employee.hire_date})"
        )
    
    # Check if already exists
    existing = crud_attendance.get_by_employee_and_date(
        db,
        employee_id=attendance_in.employee_id,
        attendance_date=attendance_in.date
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance record already exists for {attendance_in.date}"
        )
    
    attendance = crud_attendance.create(db, obj_in=attendance_in)
    
    working_hours = None
    if attendance.check_in_time and attendance.check_out_time:
        check_in = datetime.combine(date.today(), attendance.check_in_time)
        check_out = datetime.combine(date.today(), attendance.check_out_time)
        working_hours = (check_out - check_in).total_seconds() / 3600
    
    return AttendanceResponse(
        **attendance.__dict__,
        attendance_date=attendance.date,
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
    current_user: User = Depends(PermissionDependencies.can_update_attendance)
):
    """
    Update attendance record
    Permissions: Admin, Manager
    """
    attendance = crud_attendance.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    attendance = crud_attendance.update(
        db, db_obj=attendance, obj_in=attendance_in
    )

    employee = crud_employee.get(db, id=attendance.employee_id)

    working_hours = None
    if attendance.check_in_time and attendance.check_out_time:
        check_in = datetime.combine(date.today(), attendance.check_in_time)
        check_out = datetime.combine(date.today(), attendance.check_out_time)
        working_hours = (check_out - check_in).total_seconds() / 3600

    return AttendanceResponse(
        **attendance.__dict__,
        attendance_date=attendance.date,
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
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    report = crud_attendance.get_monthly_report(
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
                attendance_date=att.date,
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
    summary = crud_attendance.get_daily_summary(
        db, attendance_date=attendance_date, department_id=department_id
    )
    
    return AttendanceSummary(**summary)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_id: int,
    current_user: User = Depends(PermissionDependencies.can_delete_attendance)
):
    """
    Delete attendance record
    Permissions: Admin only
    """
    attendance = crud_attendance.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    crud_attendance.delete(db, id=attendance_id)
    return None


@router.get("/my-attendances", response_model=List[AttendanceResponse])
def get_my_attendances(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's attendance records.
    
    Permissions: All authenticated users with employee_id
    
    Query Parameters:
      start_date: Filter from this date (YYYY-MM-DD)
      end_date: Filter to this date (YYYY-MM-DD)
      skip: Number of records to skip
      limit: Maximum records to return
      
    Returns:
      List of current user's attendance records
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for current user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    attendances = crud_attendance.get_by_employee(
        db,
        employee_id=current_user.employee_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    # Add employee info to response
    result = []
    for att in attendances:
        # Calculate working hours
        working_hours = None
        if att.check_in_time and att.check_out_time:
            check_in = datetime.combine(date.today(), att.check_in_time)
            check_out = datetime.combine(date.today(), att.check_out_time)
            working_hours = (check_out - check_in).total_seconds() / 3600
        
        att_dict = att.__dict__.copy()
        att_dict['attendance_date'] = att.date
        att_dict['employee_name'] = employee.full_name
        att_dict['employee_code'] = employee.employee_code
        att_dict['department_name'] = employee.department.name if employee.department else None
        att_dict['working_hours'] = working_hours
        result.append(AttendanceResponse(**att_dict))
    
    return result
