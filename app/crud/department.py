"""
Department CRUD Operations
===========================
Extends the base CRUD class with Department-specific queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    """
    CRUD operations for Department model.
    Inherits standard operations (get, get_multi, create, update, delete)
    from CRUDBase. Adds Department-specific queries here if needed.
    """
    
    def get_by_name(self, db: Session, name: str) -> Optional[Department]:
        """
        Get department by name.
        
        SQL equivalent: SELECT * FROM departments WHERE name = ?
        
        Useful for lookups and checking duplicates before insert.
        """
        return db.query(Department).filter(Department.name == name).first()


# Create a global instance to use throughout the app
department = CRUDDepartment(Department)
