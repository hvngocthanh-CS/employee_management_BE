from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from decimal import Decimal
from datetime import date
from app.crud.base import CRUDBase
from app.models.salary import Salary
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.salary import SalaryCreate, SalaryUpdate


class CRUDSalary(CRUDBase[Salary, SalaryCreate, SalaryUpdate]):
    """CRUD operations cho Salary với advanced queries"""
    
    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Salary]:
        """Get all salary records của một nhân viên"""
        return db.query(Salary)\
            .filter(Salary.employee_id == employee_id)\
            .order_by(Salary.effective_from.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_current_salary(
        self,
        db: Session,
        employee_id: int,
        as_of_date: Optional[date] = None
    ) -> Optional[Salary]:
        """
        Get lương hiện tại của nhân viên
        as_of_date: ngày tính lương (default = today)
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        return db.query(Salary)\
            .filter(
                and_(
                    Salary.employee_id == employee_id,
                    Salary.effective_from <= as_of_date,
                    or_(
                        Salary.effective_to.is_(None),
                        Salary.effective_to >= as_of_date
                    )
                )
            )\
            .order_by(Salary.effective_from.desc())\
            .first()
    
    def get_salary_history(
        self,
        db: Session,
        employee_id: int
    ) -> List[Salary]:
        """Get toàn bộ lịch sử lương của nhân viên"""
        return db.query(Salary)\
            .filter(Salary.employee_id == employee_id)\
            .order_by(Salary.effective_from.desc())\
            .all()
    
    def update_current_salary(
        self,
        db: Session,
        employee_id: int,
        new_salary: Decimal,
        effective_from: date
    ) -> Salary:
        """
        Cập nhật lương mới cho nhân viên
        Tự động đóng record lương cũ và tạo record mới
        """
        # Lấy lương hiện tại
        current = self.get_current_salary(db, employee_id)
        
        if current:
            # Đóng lương cũ
            current.effective_to = effective_from
            db.add(current)
        
        # Tạo lương mới
        new_salary_record = Salary(
            employee_id=employee_id,
            base_salary=new_salary,
            effective_from=effective_from,
            effective_to=None
        )
        db.add(new_salary_record)
        db.commit()
        db.refresh(new_salary_record)
        
        return new_salary_record
    
    def get_salary_statistics(
        self,
        db: Session,
        department_id: Optional[int] = None
    ) -> dict:
        """
        Thống kê lương theo phòng ban
        """
        query = db.query(
            Department.id.label('department_id'),
            Department.name.label('department_name'),
            func.avg(Salary.base_salary).label('avg_salary'),
            func.min(Salary.base_salary).label('min_salary'),
            func.max(Salary.base_salary).label('max_salary'),
            func.count(func.distinct(Salary.employee_id)).label('employee_count')
        )\
        .join(Employee, Salary.employee_id == Employee.id)\
        .join(Department, Employee.department_id == Department.id)\
        .filter(Salary.effective_to.is_(None))  # Chỉ tính lương hiện tại
        
        if department_id:
            query = query.filter(Department.id == department_id)
        
        query = query.group_by(Department.id, Department.name)
        
        results = query.all()
        
        return [
            {
                "department_id": row.department_id,
                "department_name": row.department_name,
                "average_salary": float(row.avg_salary) if row.avg_salary else 0,
                "min_salary": float(row.min_salary) if row.min_salary else 0,
                "max_salary": float(row.max_salary) if row.max_salary else 0,
                "total_employees": row.employee_count
            }
            for row in results
        ]
    
    def get_employees_by_salary_range(
        self,
        db: Session,
        min_salary: Decimal,
        max_salary: Decimal,
        skip: int = 0,
        limit: int = 100
    ) -> List[Salary]:
        """Get employees trong khoảng lương"""
        return db.query(Salary)\
            .filter(
                and_(
                    Salary.effective_to.is_(None),
                    Salary.base_salary >= min_salary,
                    Salary.base_salary <= max_salary
                )
            )\
            .offset(skip)\
            .limit(limit)\
            .all()


salary = CRUDSalary(Salary)