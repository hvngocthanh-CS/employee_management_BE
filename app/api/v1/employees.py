from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_manager_or_admin
from app.models.user import User
from app.models.employee import EmploymentStatus
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse
)
from app.crud import employee as crud_employee

router = APIRouter()


@router.get("/", response_model=EmployeeListResponse)
def list_employees(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    position_id: Optional[int] = None,
    employment_status: Optional[EmploymentStatus] = None
):
    """
    List employees với filtering và pagination
    - keyword: tìm kiếm trong name, email, employee_code
    - department_id: lọc theo phòng ban
    - position_id: lọc theo chức vụ
    - employment_status: lọc theo trạng thái
    """
    employees, total = crud_employee.employee.search(
        db,
        keyword=keyword,
        department_id=department_id,
        position_id=position_id,
        employment_status=employment_status,
        skip=skip,
        limit=limit
    )
    
    # Convert to response format
    employee_responses = []
    for emp in employees:
        emp_dict = {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "full_name": emp.full_name,
            "email": emp.email,
            "phone": emp.phone,
            "date_of_birth": emp.date_of_birth,
            "gender": emp.gender,
            "address": emp.address,
            "city": emp.city,
            "department_id": emp.department_id,
            "position_id": emp.position_id,
            "hire_date": emp.hire_date,
            "employment_status": emp.employment_status,
            "created_at": emp.created_at,
            "updated_at": emp.updated_at,
            "department_name": emp.department.name if emp.department else None,
            "position_title": emp.position.title if emp.position else None
        }
        employee_responses.append(EmployeeResponse(**emp_dict))
    
    return EmployeeListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        employees=employee_responses
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get employee by ID"""
    employee = crud_employee.employee.get_with_relations(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return EmployeeResponse(
        **employee.__dict__,
        department_name=employee.department.name if employee.department else None,
        position_title=employee.position.title if employee.position else None
    )


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    *,
    db: Session = Depends(get_db),
    employee_in: EmployeeCreate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Create new employee
    Yêu cầu role MANAGER hoặc ADMIN
    """
    # Check if employee_code exists
    existing = crud_employee.employee.get_by_code(db, employee_code=employee_in.employee_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee code already exists"
        )
    
    # Check if email exists
    existing_email = crud_employee.employee.get_by_email(db, email=employee_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    employee = crud_employee.employee.create(db, obj_in=employee_in)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    employee_in: EmployeeUpdate,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Update employee
    Yêu cầu role MANAGER hoặc ADMIN
    """
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check email uniqueness if updating
    if employee_in.email and employee_in.email != employee.email:
        existing_email = crud_employee.employee.get_by_email(db, email=employee_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    employee = crud_employee.employee.update(db, db_obj=employee, obj_in=employee_in)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Delete employee (soft delete bằng cách set status = TERMINATED)
    Yêu cầu role MANAGER hoặc ADMIN
    """
    employee = crud_employee.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Soft delete
    employee.employment_status = EmploymentStatus.TERMINATED
    db.commit()
    
    return None


@router.get("/statistics/by-department", response_model=List[dict])
def get_department_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Thống kê số lượng nhân viên theo phòng ban
    """
    return crud_employee.employee.get_department_statistics(db)