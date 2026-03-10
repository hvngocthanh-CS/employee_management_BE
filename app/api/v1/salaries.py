from typing import List, Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import check_resource_ownership, PermissionDependencies
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


# =====================================================
# ENDPOINTS FOR EMPLOYEES TO VIEW THEIR OWN SALARY
# =====================================================

@router.get("/me", response_model=List[SalaryResponse])
def get_my_salaries(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user)
):
    """
    Get all salary records of current user.
    
    Permissions: All authenticated users (employees can view their own salary)
    
    Returns:
      List of salary records for the current user
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for this user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    salaries = crud_salary.get_by_employee(
        db, employee_id=current_user.employee_id, skip=skip, limit=limit
    )
    
    result = []
    for sal in salaries:
        sal_dict = sal.__dict__.copy()
        sal_dict['employee_name'] = employee.full_name
        sal_dict['employee_code'] = employee.employee_code
        result.append(SalaryResponse(**sal_dict))
    
    return result


@router.get("/me/current", response_model=SalaryResponse)
def get_my_current_salary(
    *,
    db: Session = Depends(get_db),
    as_of_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get current salary of current user.
    
    Permissions: All authenticated users (employees can view their own salary)
    
    Returns:
      Current salary of the logged-in user
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for this user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    salary = crud_salary.get_current_salary(
        db, employee_id=current_user.employee_id, as_of_date=as_of_date
    )
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current salary found"
        )
    
    return SalaryResponse(
        **salary.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code
    )


@router.get("/me/history", response_model=SalaryHistory)
def get_my_salary_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get salary history of current user.
    
    Permissions: All authenticated users (employees can view their own salary)
    
    Returns:
      Complete salary history of the logged-in user
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for this user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    salaries = crud_salary.get_salary_history(db, employee_id=current_user.employee_id)
    
    # Get current salary
    current = crud_salary.get_current_salary(db, employee_id=current_user.employee_id)
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
        employee_id=current_user.employee_id,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        salaries=salary_responses,
        current_salary=current_amount
    )


# =====================================================
# ENDPOINTS FOR ADMIN/MANAGER TO VIEW ALL SALARIES
# =====================================================

@router.get("/", response_model=List[SalaryResponse])
def list_all_salaries(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    employee_id: Optional[int] = None,
    current_user: User = Depends(PermissionDependencies.can_read_salary)
):
    """
    List all salary records (Admin/Manager only)
    Permissions: Admin, Manager
    
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      employee_id: Filter by specific employee (optional)
    """
    # Admin/Manager can view all salaries
    if employee_id:
        salaries = crud_salary.get_by_employee(db, employee_id=employee_id, skip=skip, limit=limit)
    else:
        # Get all salaries from all employees
        salaries = crud_salary.get_multi(db, skip=skip, limit=limit)
    
    # Add employee info to each salary
    result = []
    for salary in salaries:
        employee = crud_employee.get(db, id=salary.employee_id)
        result.append(
            SalaryResponse(
                **salary.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None
            )
        )
    
    return result


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
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check permission: Admin/Manager can view any, Employee can only view own
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own salary information"
        )
    
    salaries = crud_salary.get_by_employee(
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
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check permission: Admin/Manager can view any, Employee can only view own
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own salary information"
        )
    
    salary = crud_salary.get_current_salary(
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
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check permission: Admin/Manager can view any, Employee can only view own
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own salary information"
        )
    
    salaries = crud_salary.get_salary_history(db, employee_id=employee_id)
    
    # Get current salary
    current = crud_salary.get_current_salary(db, employee_id=employee_id)
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
    current_user: User = Depends(PermissionDependencies.can_create_salary)
):
    """
    Create new salary record
    Permissions: Admin, Manager
    """
    # Check employee exists
    employee = crud_employee.get(db, id=salary_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Validate: effective_from must be >= employee hire_date
    if employee.hire_date and salary_in.effective_from < employee.hire_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ngày hiệu lực lương ({salary_in.effective_from}) phải >= ngày thuê nhân viên ({employee.hire_date})"
        )
    
    # Check for overlapping salary periods
    existing_current = crud_salary.get_current_salary(
        db, 
        employee_id=salary_in.employee_id,
        as_of_date=salary_in.effective_from
    )
    
    if existing_current and existing_current.effective_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee already has an active salary. Please close it first."
        )
    
    salary = crud_salary.create(db, obj_in=salary_in)
    
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
    current_user: User = Depends(PermissionDependencies.can_update_salary)
):
    """
    Update salary record
    Permissions: Admin, Manager
    """
    salary = crud_salary.get(db, id=salary_id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary record not found"
        )
    
    # Validate: effective_from must be >= employee hire_date (if being updated)
    if salary_in.effective_from is not None:
        employee = crud_employee.get(db, id=salary.employee_id)
        if employee and employee.hire_date and salary_in.effective_from < employee.hire_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ngày hiệu lực lương ({salary_in.effective_from}) phải >= ngày thuê nhân viên ({employee.hire_date})"
            )
    
    salary = crud_salary.update(db, db_obj=salary, obj_in=salary_in)
    
    employee = crud_employee.get(db, id=salary.employee_id)
    
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
    current_user: User = Depends(PermissionDependencies.can_update_salary)
):
    """
    Update current salary (close old, create new)
    Permissions: Admin, Manager
    """
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    try:
        salary = crud_salary.update_current_salary(
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
    current_user: User = Depends(PermissionDependencies.can_read_salary)
):
    """
    Get salary statistics by department
    Permissions: Admin, Manager
    """
    stats = crud_salary.get_salary_statistics(db, department_id=department_id)
    
    return [SalaryStatistics(**stat) for stat in stats]


@router.delete("/{salary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_salary(
    *,
    db: Session = Depends(get_db),
    salary_id: int,
    current_user: User = Depends(PermissionDependencies.can_delete_salary)
):
    """
    Delete salary record
    Permissions: Admin only
    Note: Only delete if created by mistake, normally should set effective_to
    """
    salary = crud_salary.get(db, id=salary_id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary record not found"
        )
    
    crud_salary.delete(db, id=salary_id)
    return None


@router.get("/my-salary", response_model=SalaryResponse)
def get_my_current_salary(
    *,
    db: Session = Depends(get_db),
    as_of_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's current salary record.
    
    Permissions: All authenticated users with employee_id
    
    Query Parameters:
      as_of_date: Get salary as of specific date (YYYY-MM-DD)
      
    Returns:
      Current user's active salary record
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
    
    salary = crud_salary.get_current_salary(
        db, employee_id=current_user.employee_id, as_of_date=as_of_date
    )
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No salary record found"
        )
    
    return SalaryResponse(
        **salary.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code
    )


@router.get("/my-salaries", response_model=List[SalaryResponse])
def get_my_salary_history(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's salary history.
    
    Permissions: All authenticated users with employee_id
    
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      
    Returns:
      List of current user's salary records
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
    
    salaries = crud_salary.get_by_employee(
        db, employee_id=current_user.employee_id, skip=skip, limit=limit
    )
    
    # Add employee info to response
    result = []
    for sal in salaries:
        sal_dict = sal.__dict__.copy()
        sal_dict['employee_name'] = employee.full_name
        sal_dict['employee_code'] = employee.employee_code
        result.append(SalaryResponse(**sal_dict))
    
    return result
