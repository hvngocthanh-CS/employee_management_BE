"""
Department CRUD Operations
===========================
Extends the base CRUD class with Department-specific queries.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.crud.base import CRUDBase
from app.models.department import Department
from app.models.employee import Employee
from app.models.position import Position
from app.models.salary import Salary
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
    
    def get_with_employee_count(self, db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Get departments with employee count.
        
        SQL Learning: LEFT JOIN, COUNT, GROUP BY
        
        SQL equivalent:
            SELECT d.id, d.name, COUNT(e.id) as employee_count
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY employee_count DESC
            LIMIT ? OFFSET ?
        
        Returns:
            List of dicts with department info + employee_count
        """
        results = db.query(
            Department.id,
            Department.name,
            func.count(Employee.id).label('employee_count')
        ).outerjoin(Employee, Employee.department_id == Department.id)\
         .group_by(Department.id, Department.name)\
         .order_by(func.count(Employee.id).desc())\
         .offset(skip)\
         .limit(limit)\
         .all()
        
        return [
            {
                "id": dept_id,
                "name": dept_name,
                "employee_count": emp_count
            }
            for dept_id, dept_name, emp_count in results
        ]
    
    def search_departments(
        self, 
        db: Session,
        name: Optional[str] = None,
        min_employees: Optional[int] = None,
        max_employees: Optional[int] = None,
        min_avg_salary: Optional[float] = None,
        max_avg_salary: Optional[float] = None,
        sort_by: str = "name",
        order: str = "asc",
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        Advanced search and filtering for departments.
        
        SQL Learning Points:
        - ILIKE for case-insensitive pattern matching
        - Complex WHERE with multiple AND conditions
        - HAVING clause for filtering aggregated data
        - Dynamic ORDER BY based on parameters
        - Computed columns (aggregates)
        
        Example SQL generated:
            SELECT d.id, d.name, 
                   COUNT(e.id) as employee_count,
                   COALESCE(AVG(s.base_salary), 0) as avg_salary
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            LEFT JOIN salaries s ON s.employee_id = e.id 
                AND s.effective_to IS NULL
            WHERE d.name ILIKE '%engineering%'
            GROUP BY d.id, d.name
            HAVING COUNT(e.id) >= 5 
                AND COUNT(e.id) <= 50
                AND AVG(s.base_salary) >= 30000000
            ORDER BY employee_count DESC
            LIMIT 10 OFFSET 0
        
        Args:
            name: Search pattern for department name (case-insensitive)
            min_employees: Minimum number of employees
            max_employees: Maximum number of employees
            min_avg_salary: Minimum average salary
            max_avg_salary: Maximum average salary
            sort_by: Field to sort by ('name', 'employee_count', 'avg_salary')
            order: Sort order ('asc' or 'desc')
            skip: Records to skip (pagination)
            limit: Max records to return
            
        Returns:
            List of departments matching criteria
        """
        # Start with base query
        query = db.query(
            Department.id,
            Department.name,
            func.count(Employee.id).label('employee_count'),
            func.coalesce(func.avg(Salary.base_salary), 0).label('avg_salary')
        ).outerjoin(Employee, Employee.department_id == Department.id)\
         .outerjoin(
            Salary,
            (Salary.employee_id == Employee.id) & 
            or_(Salary.effective_to == None, Salary.effective_to >= date.today())
        ).group_by(Department.id, Department.name)
        
        # SQL WHERE clause - Filter by name (ILIKE for case-insensitive)
        # Pattern: ILIKE '%search%' matches any string containing 'search'
        if name:
            query = query.filter(Department.name.ilike(f'%{name}%'))
        
        # SQL HAVING clause - Filter aggregated results
        # HAVING is used AFTER GROUP BY to filter grouped data
        # WHERE filters rows BEFORE grouping, HAVING filters AFTER grouping
        having_conditions = []
        
        if min_employees is not None:
            having_conditions.append(func.count(Employee.id) >= min_employees)
        
        if max_employees is not None:
            having_conditions.append(func.count(Employee.id) <= max_employees)
        
        if min_avg_salary is not None:
            having_conditions.append(func.avg(Salary.base_salary) >= min_avg_salary)
        
        if max_avg_salary is not None:
            having_conditions.append(func.avg(Salary.base_salary) <= max_avg_salary)
        
        # Apply HAVING conditions
        for condition in having_conditions:
            query = query.having(condition)
        
        # SQL ORDER BY - Dynamic sorting
        # We build ORDER BY clause based on user input
        sort_column = {
            'name': Department.name,
            'employee_count': func.count(Employee.id),
            'avg_salary': func.avg(Salary.base_salary)
        }.get(sort_by, Department.name)
        
        if order.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # SQL LIMIT and OFFSET - Pagination
        # OFFSET skips first N records
        # LIMIT takes only M records
        # Example: OFFSET 10 LIMIT 5 returns records 11-15
        query = query.offset(skip).limit(limit)
        
        # Execute query and format results
        results = query.all()
        
        return [
            {
                "id": dept_id,
                "name": dept_name,
                "employee_count": emp_count,
                "avg_salary": round(float(avg_sal), 2)
            }
            for dept_id, dept_name, emp_count, avg_sal in results
        ]
    
    def get_department_statistics(self, db: Session, department_id: int) -> Optional[dict]:
        """
        Get comprehensive statistics for a single department.
        
        SQL Learning: Multiple JOINs, aggregates, subqueries
        
        Returns:
            Dictionary with department statistics including:
            - Employee count and breakdown by position
            - Salary statistics (total, avg, min, max)
            - Newest and longest-serving employees
        """
        # Check if department exists
        department = self.get(db, id=department_id)
        if not department:
            return None
        
        # Total employees
        total_employees = db.query(func.count(Employee.id))\
            .filter(Employee.department_id == department_id)\
            .scalar() or 0
        
        # Employee breakdown by position
        # SQL: SELECT p.id, p.title, COUNT(e.id)
        #      FROM positions p
        #      LEFT JOIN employees e ON e.position_id = p.id AND e.department_id = ?
        #      GROUP BY p.id, p.title
        #      HAVING COUNT(e.id) > 0
        position_breakdown = db.query(
            Position.id,
            Position.title,
            func.count(Employee.id).label('count')
        ).outerjoin(
            Employee,
            (Employee.position_id == Position.id) & (Employee.department_id == department_id)
        ).group_by(Position.id, Position.title)\
         .having(func.count(Employee.id) > 0)\
         .all()
        
        # Salary statistics
        # SQL: SELECT SUM(s.base_salary), AVG(s.base_salary), 
        #             MIN(s.base_salary), MAX(s.base_salary)
        #      FROM salaries s
        #      INNER JOIN employees e ON e.id = s.employee_id
        #      WHERE e.department_id = ? AND s.effective_to IS NULL
        salary_stats = db.query(
            func.sum(Salary.base_salary).label('total'),
            func.avg(Salary.base_salary).label('average'),
            func.min(Salary.base_salary).label('minimum'),
            func.max(Salary.base_salary).label('maximum')
        ).join(Employee, Employee.id == Salary.employee_id)\
         .filter(
            Employee.department_id == department_id,
            or_(Salary.effective_to == None, Salary.effective_to >= date.today())
        ).first()
        
        # Newest employee (most recent hire_date)
        newest_employee = db.query(Employee)\
            .filter(Employee.department_id == department_id)\
            .order_by(Employee.hire_date.desc())\
            .first()
        
        # Longest-serving employee (oldest hire_date)
        longest_serving = db.query(Employee)\
            .filter(Employee.department_id == department_id)\
            .order_by(Employee.hire_date.asc())\
            .first()
        
        # Build response
        return {
            "department_id": department_id,
            "department_name": department.name,
            "total_employees": total_employees,
            "employee_breakdown_by_position": [
                {
                    "position_id": pos_id,
                    "position_title": pos_title,
                    "count": count
                }
                for pos_id, pos_title, count in position_breakdown
            ],
            "salary_stats": {
                "total_salary_budget": float(salary_stats.total or 0),
                "average_salary": float(salary_stats.average or 0),
                "min_salary": float(salary_stats.minimum or 0),
                "max_salary": float(salary_stats.maximum or 0)
            },
            "newest_employee": {
                "id": newest_employee.id if newest_employee else None,
                "name": newest_employee.full_name if newest_employee else "N/A",
                "hire_date": newest_employee.hire_date.isoformat() if newest_employee and newest_employee.hire_date else None
            } if newest_employee else None,
            "longest_serving_employee": {
                "id": longest_serving.id if longest_serving else None,
                "name": longest_serving.full_name if longest_serving else "N/A",
                "hire_date": longest_serving.hire_date.isoformat() if longest_serving and longest_serving.hire_date else None
            } if longest_serving else None
        }
    
    def compare_departments(
        self,
        db: Session,
        department_ids: List[int]
    ) -> dict:
        """
        Compare multiple departments side-by-side.
        
        SQL Learning Points:
        - Window Functions: ROW_NUMBER(), RANK()
        - PARTITION BY vs GROUP BY
        - Multiple aggregations in single query
        - WHERE IN clause for multiple IDs
        - Subqueries for ranking
        
        Example SQL with Window Functions:
            SELECT 
                d.id,
                d.name,
                COUNT(e.id) as employee_count,
                COALESCE(AVG(s.base_salary), 0) as avg_salary,
                ROW_NUMBER() OVER (ORDER BY COUNT(e.id) DESC) as rank_by_size,
                ROW_NUMBER() OVER (ORDER BY AVG(s.base_salary) DESC) as rank_by_salary
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            LEFT JOIN salaries s ON s.employee_id = e.id 
                AND s.effective_to IS NULL
            WHERE d.id IN (1, 2, 3)
            GROUP BY d.id, d.name
        
        Window Functions vs GROUP BY:
        - GROUP BY: Reduces rows to one per group
        - Window Functions: Keeps all rows, adds computed column
        - ROW_NUMBER() assigns sequential numbers
        - RANK() allows ties (same values get same rank)
        
        Args:
            department_ids: List of department IDs to compare
            
        Returns:
            Comparison data with rankings
        """
        if not department_ids:
            return {"comparison": [], "summary": {}}
        
        # Subquery approach: First get department stats
        # Then rank them with window functions
        from sqlalchemy import literal_column
        
        # Get basic stats for selected departments
        stats_query = db.query(
            Department.id,
            Department.name,
            func.count(Employee.id).label('employee_count'),
            func.coalesce(func.sum(Salary.base_salary), 0).label('total_salary'),
            func.coalesce(func.avg(Salary.base_salary), 0).label('avg_salary'),
            func.count(func.distinct(Employee.position_id)).label('unique_positions')
        ).outerjoin(Employee, Employee.department_id == Department.id)\
         .outerjoin(
            Salary,
            (Salary.employee_id == Employee.id) & 
            or_(Salary.effective_to == None, Salary.effective_to >= date.today())
        ).filter(Department.id.in_(department_ids))\
         .group_by(Department.id, Department.name)\
         .all()
        
        # Convert to list of dicts for ranking
        dept_data = [
            {
                "department_id": row[0],
                "department_name": row[1],
                "total_employees": row[2],
                "total_salary_budget": float(row[3]),
                "avg_salary": float(row[4]),
                "unique_positions": row[5]
            }
            for row in stats_query
        ]
        
        # Manual ranking (simpler than window functions for small datasets)
        # In production, use window functions for efficiency
        # This demonstrates the ranking logic
        
        # Sort by employee count for size ranking
        sorted_by_size = sorted(dept_data, key=lambda x: x['total_employees'], reverse=True)
        for rank, dept in enumerate(sorted_by_size, 1):
            dept['rank_by_size'] = rank
        
        # Sort by average salary for salary ranking
        sorted_by_salary = sorted(dept_data, key=lambda x: x['avg_salary'], reverse=True)
        for rank, dept in enumerate(sorted_by_salary, 1):
            dept['rank_by_salary'] = rank
        
        # Create summary
        summary = {}
        if dept_data:
            largest = max(dept_data, key=lambda x: x['total_employees'])
            highest_paid = max(dept_data, key=lambda x: x['avg_salary'])
            most_diverse = max(dept_data, key=lambda x: x['unique_positions'])
            
            summary = {
                "largest_department": largest['department_name'],
                "highest_paid_department": highest_paid['department_name'],
                "most_diverse_positions": most_diverse['department_name']
            }
        
        return {
            "comparison": dept_data,
            "summary": summary
        }
    
    def get_department_employees(
        self,
        db: Session,
        department_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "name",
        order: str = "asc",
        position_id: Optional[int] = None
    ) -> dict:
        """
        Get employees of a department with pagination.
        
        SQL Learning Points:
        - OFFSET and LIMIT for pagination
        - COUNT(*) OVER() window function (total without separate query)
        - Multiple JOINs (employees → departments, positions, salaries)
        - Dynamic WHERE clause
        - Pagination formula: OFFSET = (page - 1) * page_size
        
        Example SQL with COUNT(*) OVER() window function:
            SELECT 
                e.id,
                e.name,
                e.email,
                p.title as position,
                e.hire_date,
                s.base_salary as current_salary,
                COUNT(*) OVER() as total_count  -- Window function: total without GROUP BY
            FROM employees e
            INNER JOIN departments d ON d.id = e.department_id
            LEFT JOIN positions p ON p.id = e.position_id
            LEFT JOIN salaries s ON s.employee_id = e.id 
                AND s.effective_to IS NULL
            WHERE e.department_id = 1
                AND e.position_id = 2  -- Optional filter
            ORDER BY e.name ASC
            LIMIT 10 OFFSET 0
        
        Pagination Logic:
        - Page 1: OFFSET 0, LIMIT 10  (records 1-10)
        - Page 2: OFFSET 10, LIMIT 10 (records 11-20)
        - Page 3: OFFSET 20, LIMIT 10 (records 21-30)
        - Formula: OFFSET = (page - 1) * page_size
        
        Args:
            department_id: Department ID
            page: Page number (1-indexed)
            page_size: Records per page
            sort_by: Sort field ('name', 'hire_date', 'salary')
            order: 'asc' or 'desc'
            position_id: Optional position filter
            
        Returns:
            Paginated employee list with metadata
        """
        # Check if department exists
        dept = self.get(db, id=department_id)
        if not dept:
            return None
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Base query with JOINs
        query = db.query(
            Employee.id,
            Employee.full_name,
            Employee.email,
            Employee.hire_date,
            Position.title.label('position'),
            func.coalesce(Salary.base_salary, 0).label('current_salary')
        ).filter(Employee.department_id == department_id)\
         .outerjoin(Position, Position.id == Employee.position_id)\
         .outerjoin(
            Salary,
            (Salary.employee_id == Employee.id) & 
            or_(Salary.effective_to == None, Salary.effective_to >= date.today())
        )
        
        # Optional filter by position
        if position_id:
            query = query.filter(Employee.position_id == position_id)
        
        # Dynamic ORDER BY
        sort_column = {
            'name': Employee.full_name,
            'hire_date': Employee.hire_date,
            'salary': Salary.base_salary
        }.get(sort_by, Employee.full_name)
        
        if order.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count BEFORE applying pagination
        # This requires a separate query (in production, use COUNT(*) OVER())
        total_count = query.count()
        
        # Apply pagination
        results = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        import math
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0
        
        # Format results
        employees = [
            {
                "id": emp_id,
                "name": emp_name,
                "email": emp_email,
                "position": pos_title or "N/A",
                "hire_date": hire_date.isoformat() if hire_date else None,
                "current_salary": float(salary)
            }
            for emp_id, emp_name, emp_email, hire_date, pos_title, salary in results
        ]
        
        return {
            "department_id": department_id,
            "department_name": dept.name,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_count,
                "total_pages": total_pages
            },
            "employees": employees
        }


# Create a global instance to use throughout the app
department = CRUDDepartment(Department)
