from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentResponse, DepartmentCreate, DepartmentUpdate
from app.core.deps import get_current_user, require_admin
from app import crud

router = APIRouter()


@router.get("/")
def list_departments(db: Session = Depends(get_db)):
    """
    List all departments - đơn giản cho WPF
    """
    departments = db.query(Department).all()
    return {"data": [{
        "id": d.id,
        "name": d.name,
        "code": d.code,
        "description": d.description
    } for d in departments], "total": len(departments)}


@router.post("/")
def create_department(department_in: dict, db: Session = Depends(get_db)):
    """
    Create department - đơn giản cho WPF
    """
    new_department = Department(
        name=department_in.get("name"),
        description=department_in.get("description", "")
    )
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    return {
        "message": "Department created successfully",
        "id": new_department.id,
        "name": new_department.name,
        "description": new_department.description
    }


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    *,
    db: Session = Depends(get_db),
    department_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get department by ID"""
    department = crud.department.get(db, id=department_id)
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
    existing = crud.department.get_by_code(db, code=department_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    
    department = crud.department.create(db, obj_in=department_in)
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
    department = crud.department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check code uniqueness if updating
    if department_in.code and department_in.code != department.code:
        existing = crud.department.get_by_code(db, code=department_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists"
            )
    
    department = crud.department.update(db, db_obj=department, obj_in=department_in)
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
    department = crud.department.get(db, id=department_id)
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
    
    crud.department.delete(db, id=department_id)
    return None