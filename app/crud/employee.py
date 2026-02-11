from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, and_, func, case
from datetime import date, datetime
from app.crud.base import CRUDBase
from app.models.employee import Employee, EmploymentStatus
from app.models.department import Department
from app.models.position import Position
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """
    CRUD operations cho Employee với advanced queries
    """
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Employee]:
        """
        Get employee với eager loading relationships
        Tránh N+1 query problem
        """
        return db.query(Employee)\
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.user)
            )\
            .filter(Employee.id == id)\
            .first()
    
    def get_by_code(self, db: Session, employee_code: str) -> Optional[Employee]:
        """Get employee by employee_code"""
        return db.query(Employee)\
            .filter(Employee.employee_code == employee_code)\
            .first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """Get employee by email"""
        return db.query(Employee)\
            .filter(Employee.email == email)\
            .first()
    
    def search(
        self,
        db: Session,
        *,
        keyword: Optional[str] = None,
        department_id: Optional[int] = None,
        position_id: Optional[int] = None,
        employment_status: Optional[EmploymentStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Employee], int]:
        """
        Advanced search với multiple filters
        Returns: (employees, total_count)
        """
        query = db.query(Employee).options(
            selectinload(Employee.department),
            selectinload(Employee.position)
        )
        
        # Keyword search: tìm trong name, email, employee_code
        if keyword:
            keyword_filter = or_(
                Employee.full_name.ilike(f"%{keyword}%"),
                Employee.email.ilike(f"%{keyword}%"),
                Employee.employee_code.ilike(f"%{keyword}%")
            )
            query = query.filter(keyword_filter)
        
        # Filter by department
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        # Filter by position
        if position_id:
            query = query.filter(Employee.position_id == position_id)
        
        # Filter by employment status
        if employment_status:
            query = query.filter(Employee.employment_status == employment_status)
        
        # Count total before pagination
        total = query.count()
        
        # Apply pagination
        employees = query.offset(skip).limit(limit).all()
        
        return employees, total
    
    def get_active_employees(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get all active employees"""
        return db.query(Employee)\
            .filter(Employee.employment_status == EmploymentStatus.ACTIVE)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_employees_by_department(
        self,
        db: Session,
        department_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees by department"""
        return db.query(Employee)\
            .filter(Employee.department_id == department_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_new_hires(
        self,
        db: Session,
        from_date: date,
        to_date: Optional[date] = None
    ) -> List[Employee]:
        """
        Get employees hired trong khoảng thời gian
        """
        query = db.query(Employee)\
            .filter(Employee.hire_date >= from_date)
        
        if to_date:
            query = query.filter(Employee.hire_date <= to_date)
        
        return query.order_by(Employee.hire_date.desc()).all()
    
    def get_department_statistics(self, db: Session) -> List[dict]:
        """
        Query statistics: số lượng nhân viên theo phòng ban
        Sử dụng GROUP BY và aggregate functions
        """
        result = db.query(
            Department.id,
            Department.name,
            func.count(Employee.id).label('employee_count'),
            func.count(
                case((Employee.employment_status == EmploymentStatus.ACTIVE, 1))
            ).label('active_count')
        )\
        .outerjoin(Employee, Department.id == Employee.department_id)\
        .group_by(Department.id, Department.name)\
        .all()
        
        return [
            {
                "department_id": row.id,
                "department_name": row.name,
                "total_employees": row.employee_count,
                "active_employees": row.active_count
            }
            for row in result
        ]


employee = CRUDEmployee(Employee)