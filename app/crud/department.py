from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    """CRUD operations cho Department"""
    
    def get_by_code(self, db: Session, code: str) -> Optional[Department]:
        """Get department by code"""
        return db.query(Department).filter(Department.code == code).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Department]:
        """Get department by name"""
        return db.query(Department).filter(Department.name == name).first()


department = CRUDDepartment(Department)