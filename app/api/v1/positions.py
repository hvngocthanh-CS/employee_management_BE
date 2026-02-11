from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.models.position import PositionLevel
from app.schemas.position import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionWithStats
)
from app.crud import position as crud_position

router = APIRouter()


@router.get("/", response_model=List[PositionWithStats])
def list_positions(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[PositionLevel] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all positions với employee statistics
    """
    if level:
        positions_data = crud_position.position.get_by_level(
            db, level=level, skip=skip, limit=limit
        )
        # Convert to stats format
        result = []
        for pos in positions_data:
            result.append(
                PositionWithStats(
                    **pos.__dict__,
                    employee_count=0,
                    active_employee_count=0
                )
            )
        return result
    else:
        positions_with_stats = crud_position.position.get_with_employee_stats(db)
        
        result = []
        for item in positions_with_stats:
            pos_dict = {
                "id": item["position"].id,
                "title": item["position"].title,
                "code": item["position"].code,
                "level": item["position"].level,
                "description": item["position"].description,
                "employee_count": item["employee_count"],
                "active_employee_count": item["active_employee_count"]
            }
            result.append(PositionWithStats(**pos_dict))
        
        return result[skip:skip+limit]


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    *,
    db: Session = Depends(get_db),
    position_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get position by ID"""
    position = crud_position.position.get(db, id=position_id)
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
    current_user: User = Depends(require_admin)
):
    """
    Create new position
    Yêu cầu role ADMIN
    """
    # Check if code exists
    existing = crud_position.position.get_by_code(db, code=position_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position code already exists"
        )
    
    position = crud_position.position.create(db, obj_in=position_in)
    return position


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    *,
    db: Session = Depends(get_db),
    position_id: int,
    position_in: PositionUpdate,
    current_user: User = Depends(require_admin)
):
    """
    Update position
    Yêu cầu role ADMIN
    """
    position = crud_position.position.get(db, id=position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Check code uniqueness if updating
    if position_in.code and position_in.code != position.code:
        existing = crud_position.position.get_by_code(db, code=position_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position code already exists"
            )
    
    position = crud_position.position.update(db, db_obj=position, obj_in=position_in)
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    *,
    db: Session = Depends(get_db),
    position_id: int,
    current_user: User = Depends(require_admin)
):
    """
    Delete position
    Yêu cầu role ADMIN
    """
    position = crud_position.position.get(db, id=position_id)
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
    
    crud_position.position.delete(db, id=position_id)
    return None