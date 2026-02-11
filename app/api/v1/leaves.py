from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_manager_or_admin
from app.models.user import User, UserRole
from app.models.leave import LeaveStatus
from app.schemas.leave import (
    LeaveCreate,
    LeaveUpdate,
    LeaveApproval,
    LeaveCancel,
    LeaveResponse,
    LeaveListResponse,
    LeaveBalance,
    LeaveStatistics,
    LeaveCalendar
)
from app.crud import leave as crud_leave, employee as crud_employee

router = APIRouter()


@router.get("/", response_model=LeaveListResponse)
def list_leaves(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    status: Optional[LeaveStatus] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all leaves
    Admin/Manager: xem tất cả
    Employee: chỉ xem của mình
    """
    # Get total count
    filters = {}
    if status:
        filters['status'] = status
    
    if current_user.role == UserRole.EMPLOYEE:
        # Employee chỉ xem leaves của mình
        leaves = crud_leave.leave.get_by_employee(
            db,
            employee_id=current_user.employee_id,
            status=status,
            skip=skip,
            limit=limit
        )
        total = crud_leave.leave.count(
            db,
            filters={'employee_id': current_user.employee_id, **filters}
        )
    else:
        # Admin/Manager xem tất cả
        if status:
            filters['status'] = status
        
        leaves = crud_leave.leave.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
        total = crud_leave.leave.count(db, filters=filters)
    
    # Convert to response format
    leave_responses = []
    for leave in leaves:
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        approver_name = None
        if leave.approved_by:
            from app.crud import user as crud_user
            approver = crud_user.user.get(db, id=leave.approved_by)
            if approver and approver.employee:
                approver_name = approver.employee.full_name
        
        leave_responses.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None,
                approver_name=approver_name
            )
        )
    
    return LeaveListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        leaves=leave_responses
    )


@router.get("/pending", response_model=List[LeaveResponse])
def get_pending_leaves(
    *,
    db: Session = Depends(get_db),
    department_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Get leaves đang chờ duyệt
    Yêu cầu role MANAGER hoặc ADMIN
    """
    leaves = crud_leave.leave.get_pending_leaves(
        db, department_id=department_id, skip=skip, limit=limit
    )
    
    result = []
    for leave in leaves:
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        result.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None
            )
        )
    
    return result


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get leave by ID"""
    leave = crud_leave.leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if leave.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own leave requests"
            )
    
    employee = crud_employee.employee.get(db, id=leave.employee_id)
    
    approver_name = None
    if leave.approved_by:
        from app.crud import user as crud_user
        approver = crud_user.user.get(db, id=leave.approved_by)
        if approver and approver.employee:
            approver_name = approver.employee.full_name
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department.name if employee and employee.department else None,
        approver_name=approver_name
    )


@router.post("/", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def create_leave(
    *,
    db: Session = Depends(get_db),
    leave_in: LeaveCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Tạo đơn nghỉ phép
    Employee chỉ được tạo cho chính mình
    """
    # Check employee exists
    employee = crud_employee.employee.get(db, id=leave_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Employee chỉ được tạo leave cho chính mình
    if current_user.role == UserRole.EMPLOYEE:
        if leave_in.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create leave requests for yourself"
            )
    
    # Check for conflicts
    has_conflict = crud_leave.leave.check_leave_conflict(
        db,
        employee_id=leave_in.employee_id,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date
    )
    
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave request conflicts with existing leave"
        )
    
    leave = crud_leave.leave.create(db, obj_in=leave_in)
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        department_name=employee.department.name if employee.department else None
    )


@router.put("/{leave_id}", response_model=LeaveResponse)
def update_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    leave_in: LeaveUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update leave request (chỉ khi status = PENDING)
    Employee chỉ được update của mình
    """
    leave = crud_leave.leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if leave.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own leave requests"
            )
    
    # Chỉ update được khi PENDING
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update leave with status: {leave.status}"
        )
    
    # Check conflicts if updating dates
    if leave_in.start_date or leave_in.end_date:
        start = leave_in.start_date or leave.start_date
        end = leave_in.end_date or leave.end_date
        
        has_conflict = crud_leave.leave.check_leave_conflict(
            db,
            employee_id=leave.employee_id,
            start_date=start,
            end_date=end,
            exclude_leave_id=leave_id
        )
        
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave request conflicts with existing leave"
            )
    
    leave = crud_leave.leave.update(db, db_obj=leave, obj_in=leave_in)
    
    employee = crud_employee.employee.get(db, id=leave.employee_id)
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department.name if employee and employee.department else None
    )


@router.post("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Duyệt đơn nghỉ phép
    Yêu cầu role MANAGER hoặc ADMIN
    """
    try:
        leave = crud_leave.leave.approve_leave(
            db, leave_id=leave_id, approver_id=current_user.id
        )
        
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None,
            approver_name=current_user.employee.full_name if current_user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Từ chối đơn nghỉ phép
    Yêu cầu role MANAGER hoặc ADMIN
    """
    try:
        leave = crud_leave.leave.reject_leave(
            db, leave_id=leave_id, approver_id=current_user.id
        )
        
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None,
            approver_name=current_user.employee.full_name if current_user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{leave_id}/cancel", response_model=LeaveResponse)
def cancel_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(get_current_user)
):
    """Hủy đơn nghỉ phép (employee tự hủy)"""
    try:
        leave = crud_leave.leave.cancel_leave(
            db, leave_id=leave_id, employee_id=current_user.employee_id
        )
        
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/balance/{employee_id}", response_model=LeaveBalance)
def get_leave_balance(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    year: int = Query(default_factory=lambda: date.today().year),
    current_user: User = Depends(get_current_user)
):
    """Get số ngày phép còn lại"""
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own leave balance"
            )
    
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    balance = crud_leave.leave.get_leave_balance(
        db, employee_id=employee_id, year=year
    )
    
    return LeaveBalance(
        employee_id=employee_id,
        employee_name=employee.full_name,
        year=year,
        **balance
    )


@router.get("/statistics/monthly", response_model=LeaveStatistics)
def get_leave_statistics(
    *,
    db: Session = Depends(get_db),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    department_id: Optional[int] = None,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Thống kê nghỉ phép theo tháng
    Yêu cầu role MANAGER hoặc ADMIN
    """
    stats = crud_leave.leave.get_leave_statistics(
        db, month=month, year=year, department_id=department_id
    )
    
    return LeaveStatistics(**stats)


@router.get("/calendar/{target_date}", response_model=LeaveCalendar)
def get_leave_calendar(
    *,
    db: Session = Depends(get_db),
    target_date: date,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Lịch nghỉ phép trong một ngày"""
    calendar = crud_leave.leave.get_leave_calendar(
        db, target_date=target_date, department_id=department_id
    )
    
    # Convert leaves to response format
    leave_responses = []
    for leave in calendar["leaves"]:
        employee = crud_employee.employee.get(db, id=leave.employee_id)
        leave_responses.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None
            )
        )
    
    return LeaveCalendar(
        date=target_date,
        total_on_leave=calendar["total_on_leave"],
        leaves=leave_responses
    )


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Delete leave request (hard delete)
    Yêu cầu role MANAGER hoặc ADMIN
    Thường nên dùng cancel thay vì delete
    """
    leave = crud_leave.leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    crud_leave.leave.delete(db, id=leave_id)
    return None