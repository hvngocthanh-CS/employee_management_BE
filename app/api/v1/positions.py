from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import PermissionDependencies
from app.models.user import User
from app.models.position import PositionLevel
from app.schemas.position import (
    PositionCreate,
    PositionUpdate,
    PositionResponse
)
from app.crud import position as crud_position

router = APIRouter()


@router.get("/", response_model=List[PositionResponse])
def list_positions(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[PositionLevel] = None,
    department_id: Optional[int] = Query(None, description="Filter positions by department")
):
    """
    List all positions (no authentication required for GET).
    Optionally filter by department_id. Cross-department positions (dept=NULL) always included.
    """
    from app.models.position import Position
    from sqlalchemy import or_
    query = db.query(Position)
    if department_id is not None:
        # Include both department-specific AND cross-department (NULL) positions
        query = query.filter(or_(Position.department_id == department_id, Position.department_id.is_(None)))
    if level:
        query = query.filter(Position.level == level)
    return query.offset(skip).limit(limit).all()


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    *,
    db: Session = Depends(get_db),
    position_id: int
):
    """Get position by ID (no authentication required)"""
    position = crud_position.get(db, id=position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    return position


@router.post("/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    *,
    db: Session = Depends(get_db),
    position_in: PositionCreate,
    current_user: User = Depends(PermissionDependencies.can_create_position)
):
    """
    Create new position
    Permissions: Admin, Manager
    """
    # Check if code exists
    existing = crud_position.get_by_code(db, code=position_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position code already exists"
        )
    
    position = crud_position.create(db, obj_in=position_in)
    return position


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    *,
    db: Session = Depends(get_db),
    position_id: int,
    position_in: PositionUpdate,
    current_user: User = Depends(PermissionDependencies.can_update_position)
):
    """
    Update position
    Permissions: Admin, Manager
    """
    position = crud_position.get(db, id=position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Check code uniqueness if updating
    if position_in.code and position_in.code != position.code:
        existing = crud_position.get_by_code(db, code=position_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position code already exists"
            )
    
    position = crud_position.update(db, db_obj=position, obj_in=position_in)
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    *,
    db: Session = Depends(get_db),
    position_id: int,
    current_user: User = Depends(PermissionDependencies.can_delete_position)
):
    """
    Delete position
    Permissions: Admin only
    """
    position = crud_position.get(db, id=position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Check if position has employees
    from app.models.employee import Employee
    employee_count = db.query(Employee).filter(
        Employee.position_id == position_id
    ).count()
    
    if employee_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete position with {employee_count} employees"
        )
    
    crud_position.delete(db, id=position_id)
    return None