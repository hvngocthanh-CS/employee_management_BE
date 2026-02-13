"""
Department API Router
=====================
Endpoints for managing departments.

Demonstrates:
  - GET /departments - list all
  - GET /departments/{id} - get one
  - POST /departments - create
  - PUT /departments/{id} - update
  - DELETE /departments/{id} - delete
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.crud import department as crud_department

# Create router for department endpoints
router = APIRouter()


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all departments.
    
    Query Parameters:
      skip: Number of records to skip (default: 0)
      limit: Maximum records to return (default: 100)
      
    Returns:
      List of departments with id and name
    """
    departments = crud_department.get_multi(db, skip=skip, limit=limit)
    return departments


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department_in: DepartmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new department.
    
    Request Body:
      {
        "name": "Engineering"
      }
      
    Validation:
      - name must be unique
      - name is required
      
    Returns:
      The created department with auto-generated id
    """
    # Check if department with this name already exists
    # This prevents duplicate department names
    existing = crud_department.get_by_name(db, name=department_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{department_in.name}' already exists"
        )
    
    # Create and save the new department
    department = crud_department.create(db, obj_in=department_in)
    return department


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single department by ID.
    
    Path Parameters:
      department_id: The department's primary key
      
    Returns:
      Department data or 404 if not found
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a department.
    
    Path Parameters:
      department_id: The department's primary key
      
    Request Body (all optional):
      {
        "name": "New Department Name"
      }
      
    Returns:
      Updated department data or 404 if not found
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    
    # If new name provided, check for duplicates
    if department_in.name and department_in.name != department.name:
        existing = crud_department.get_by_name(db, name=department_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with name '{department_in.name}' already exists"
            )
    
    # Update and save
    department = crud_department.update(db, db_obj=department, obj_in=department_in)
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a department by ID.
    
    Path Parameters:
      department_id: The department's primary key
      
    Returns:
      No content (204) on successful deletion or 404 if not found
      
    Note:
      Deleting a department will cascade-delete all employees in it
      (due to cascade="all, delete-orphan" in the model)
    """
    department = crud_department.delete(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    # 204 responses don't have a body, so we just return
