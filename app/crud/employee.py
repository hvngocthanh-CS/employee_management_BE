"""
Employee CRUD Operations
========================
Extends the base CRUD class with Employee-specific queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """
    CRUD operations for Employee model.
    Inherits standard operations from CRUDBase.
    Adds Employee-specific queries here.
    """
    
    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """
        Get employee by email.
        
        SQL equivalent: SELECT * FROM employees WHERE email = ?
        
        Useful for lookups and checking for duplicate emails before insert.
        Email must be unique, so this should return at most one record.
        """
        return db.query(Employee).filter(Employee.email == email).first()


# Create a global instance to use throughout the app
employee = CRUDEmployee(Employee)
