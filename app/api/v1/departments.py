from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentWithStats
)
from app.crud.department import department as crud_department

router = APIRouter()


@router.get("/", response_model=List[DepartmentWithStats])
def list_departments(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """List all departments với employee count"""
    from sqlalchemy import func
    from app.models.department import Department
    from app.models.employee import Employee
    
    departments = db.query(
        Department,
        func.count(Employee.id).label('employee_count')
    ).outerjoin(
        Employee, Department.id == Employee.department_id
    ).group_by(
        Department.id
    ).offset(skip).limit(limit).all()
    
    result = []
    for dept, count in departments:
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "created_at": dept.created_at,
            "updated_at": dept.updated_at,
            "employee_count": count
        }
        result.append(DepartmentWithStats(**dept_dict))
    
    return result


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    *,
    db: Session = Depends(get_db),
    department_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get department by ID"""
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(require_admin)
):
    """
    Create new department
    Yêu cầu role ADMIN
    """
    # Check if code exists
    existing = crud_department.get_by_code(db, code=department_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    
    department = crud_department.create(db, obj_in=department_in)
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    *,
    db: Session = Depends(get_db),
    department_id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(require_admin)
):
    """
    Update department
    Yêu cầu role ADMIN
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check code uniqueness if updating
    if department_in.code and department_in.code != department.code:
        existing = crud_department.get_by_code(db, code=department_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists"
            )
    
    department = crud_department.update(db, db_obj=department, obj_in=department_in)
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    *,
    db: Session = Depends(get_db),
    department_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Delete department
    Yêu cầu role ADMIN
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has employees
    from app.models.employee import Employee
    employee_count = db.query(Employee).filter(
        Employee.department_id == department_id
    ).count()
    
    if employee_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department with {employee_count} employees"
        )
    
    crud_department.delete(db, id=department_id)
    return None