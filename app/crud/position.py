from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.crud.base import CRUDBase
from app.models.position import Position, PositionLevel
from app.models.employee import Employee
from app.schemas.position import PositionCreate, PositionUpdate


class CRUDPosition(CRUDBase[Position, PositionCreate, PositionUpdate]):
    """CRUD operations cho Position"""
    
    def get_by_code(self, db: Session, code: str) -> Optional[Position]:
        """Get position by code"""
        return db.query(Position).filter(Position.code == code).first()
    
    def get_by_title(self, db: Session, title: str) -> Optional[Position]:
        """Get position by title"""
        return db.query(Position).filter(Position.title == title).first()
    
    def get_by_level(
        self,
        db: Session,
        level: PositionLevel,
        skip: int = 0,
        limit: int = 100
    ) -> List[Position]:
        """Get positions by level"""
        return db.query(Position)\
            .filter(Position.level == level)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_with_employee_stats(self, db: Session) -> List[dict]:
        """
        Get positions với thống kê số lượng nhân viên
        """
        result = db.query(
            Position,
            func.count(Employee.id).label('employee_count'),
        )\
        .outerjoin(Position.employees)\
        .group_by(Position.id)\
        .all()
        
        return [
            {
                "position": row.Position,
                "employee_count": row.employee_count,
            }
            for row in result
        ]


position = CRUDPosition(Position)