"""
Employee API Router
===================
Endpoints for managing employees với role-based permissions.

Roles:
  - Admin: Toàn quyền CRUD
  - Manager: Có thể xem và chỉnh sửa employees
  - Employee: Chỉ xem thông tin cá nhân
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.crud import employee as crud_employee
from app.core.permissions import PermissionDependencies, check_resource_ownership
from app.core.deps import get_current_user
from app.models.user import User

# Create router for employee endpoints
router = APIRouter()


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_employee)
):
    """
    Get all employees (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Query Parameters:
      skip: Number of records to skip for pagination (default: 0)
      limit: Maximum records to return (default: 100)
      
    Returns:
      List of employees với full information
    """
    employees = crud_employee.get_multi(db, skip=skip, limit=limit)
    return employees


@router.get("/me", response_model=EmployeeResponse)
def get_my_employee_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's employee data.
    
    Permissions: All authenticated users
    
    Returns:
      Current user's employee information
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
    
    return employee


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_create_employee)
):
    """
    Create a new employee (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Request Body:
      {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john@example.com",
        "phone": "+1234567890",
        "department_id": 1,
        "position_id": 1,
        "hire_date": "2024-01-01",
        "salary": 50000.00
      }
      
    Validation:
      - email must be unique
      - email must be a valid email format
      - first_name and last_name are required
      
    Returns:
      The created employee với auto-generated id
    """
    # Check if email already exists
    existing = crud_employee.get_by_email(db, email=employee_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{employee_in.email}' is already registered"
        )
    
    # Create and save the new employee
    employee = crud_employee.create(db, obj_in=employee_in)
    return employee


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_own_employee_data)
):
    """
    Get a single employee by ID.
    
    Permissions: 
      - Admin/Manager: Can view any employee
      - Employee: Can only view own record
      
    Path Parameters:
      employee_id: The employee's primary key
      
    Returns:
      Employee data hoặc 403 if no permission, 404 if not found
    """
    # Check if user can access this employee record
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own employee record"
        )
    
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_update_employee)
):
    """
    Update an employee (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Path Parameters:
      employee_id: The employee's primary key
      
    Request Body:
      {
        "first_name": "Jane",  // optional
        "last_name": "Smith",  // optional
        "email": "jane.smith@example.com",  // optional
        "phone": "+0987654321",  // optional
        "department_id": 2,  // optional
        "position_id": 2,  // optional
        "salary": 55000.00  // optional
      }
      
    Returns:
      Updated employee data
    """
    # Check if employee exists
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    # Check email uniqueness if email is being updated
    if employee_in.email and employee_in.email != employee.email:
        existing = crud_employee.get_by_email(db, email=employee_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{employee_in.email}' is already registered"
            )
    
    # Update employee
    employee = crud_employee.update(db, db_obj=employee, obj_in=employee_in)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_delete_employee)
):
    """
    Delete an employee (Admin only).
    
    Permissions: Admin only
    
    Path Parameters:
      employee_id: The employee's primary key
      
    Returns:
      204 No Content on success, 404 if not found
      
    Note: 
      - This will also cascade delete related user account
      - Consider soft delete for production use
    """
    # Check if employee exists
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    # Delete employee (will cascade to user if exists)
    crud_employee.remove(db, id=employee_id)
    return None


@router.get("/search/{query}", response_model=List[EmployeeResponse])
def search_employees(
    query: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_employee)
):
    """
    Search employees by name or email (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Path Parameters:
      query: Search term (name hoặc email)
      
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      
    Returns:
      List of matching employees
    """
    employees = crud_employee.search(db, query=query, skip=skip, limit=limit)
    return employees
