from typing import List, Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_manager_or_admin
from app.models.user import User
from app.schemas.salary import (
    SalaryCreate,
    SalaryUpdate,
    SalaryResponse,
    SalaryHistory,
    SalaryStatistics
)
from app.crud import salary as crud_salary, employee as crud_employee

router = APIRouter()


@router.get("/employee/{employee_id}", response_model=List[SalaryResponse])
def get_employee_salaries(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user)
):
    """Get all salary records của một nhân viên"""
    # Check employee exists
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    salaries = crud_salary.salary.get_by_employee(
        db, employee_id=employee_id, skip=skip, limit=limit
    )
    
    # Add employee info to response
    result = []
    for sal in salaries:
        sal_dict = sal.__dict__.copy()
        sal_dict['employee_name'] = employee.full_name
        sal_dict['employee_code'] = employee.employee_code
        result.append(SalaryResponse(**sal_dict))
    
    return result


@router.get("/employee/{employee_id}/current", response_model=SalaryResponse)
def get_current_salary(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    as_of_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get lương hiện tại của nhân viên"""
    # Check employee exists
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    salary = crud_salary.salary.get_current_salary(
        db, employee_id=employee_id, as_of_date=as_of_date
    )
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current salary found for this employee"
        )
    
    return SalaryResponse(
        **salary.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code
    )


@router.get("/employee/{employee_id}/history", response_model=SalaryHistory)
def get_salary_history(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get toàn bộ lịch sử lương"""
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    salaries = crud_salary.salary.get_salary_history(db, employee_id=employee_id)
    
    # Get current salary
    current = crud_salary.salary.get_current_salary(db, employee_id=employee_id)
    current_amount = current.base_salary if current else None
    
    salary_responses = [
        SalaryResponse(
            **s.__dict__,
            employee_name=employee.full_name,
            employee_code=employee.employee_code
        )
        for s in salaries
    ]
    
    return SalaryHistory(
        employee_id=employee_id,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        salaries=salary_responses,
        current_salary=current_amount
    )


@router.post("/", response_model=SalaryResponse, status_code=status.HTTP_201_CREATED)
def create_salary(
    *,
    db: Session = Depends(get_db),
    salary_in: SalaryCreate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Create new salary record
    Yêu cầu role MANAGER hoặc ADMIN
    """
    # Check employee exists
    employee = crud_employee.employee.get(db, id=salary_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check for overlapping salary periods
    existing_current = crud_salary.salary.get_current_salary(
        db, 
        employee_id=salary_in.employee_id,
        as_of_date=salary_in.effective_from
    )
    
    if existing_current and existing_current.effective_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee already has an active salary. Please close it first."
        )
    
    salary = crud_salary.salary.create(db, obj_in=salary_in)
    
    return SalaryResponse(
        **salary.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code
    )


@router.put("/{salary_id}", response_model=SalaryResponse)
def update_salary(
    *,
    db: Session = Depends(get_db),
    salary_id: int,
    salary_in: SalaryUpdate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Update salary record
    Yêu cầu role MANAGER hoặc ADMIN
    """
    salary = crud_salary.salary.get(db, id=salary_id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary record not found"
        )
    
    salary = crud_salary.salary.update(db, db_obj=salary, obj_in=salary_in)
    
    employee = crud_employee.employee.get(db, id=salary.employee_id)
    
    return SalaryResponse(
        **salary.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None
    )


@router.post("/employee/{employee_id}/update-current", response_model=SalaryResponse)
def update_current_salary(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    new_salary: Decimal = Query(..., gt=0),
    effective_from: date = Query(default_factory=date.today),
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Cập nhật lương hiện tại (đóng lương cũ, tạo lương mới)
    Yêu cầu role MANAGER hoặc ADMIN
    """
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    try:
        salary = crud_salary.salary.update_current_salary(
            db,
            employee_id=employee_id,
            new_salary=new_salary,
            effective_from=effective_from
        )
        
        return SalaryResponse(
            **salary.__dict__,
            employee_name=employee.full_name,
            employee_code=employee.employee_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/statistics", response_model=List[SalaryStatistics])
def get_salary_statistics(
    *,
    db: Session = Depends(get_db),
    department_id: Optional[int] = None,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Thống kê lương theo phòng ban
    Yêu cầu role MANAGER hoặc ADMIN
    """
    stats = crud_salary.salary.get_salary_statistics(db, department_id=department_id)
    
    return [SalaryStatistics(**stat) for stat in stats]


@router.delete("/{salary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_salary(
    *,
    db: Session = Depends(get_db),
    salary_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Delete salary record
    Yêu cầu role MANAGER hoặc ADMIN
    Chỉ nên xóa nếu tạo nhầm, thông thường nên set effective_to
    """
    salary = crud_salary.salary.get(db, id=salary_id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary record not found"
        )
    
    crud_salary.salary.delete(db, id=salary_id)
    return None