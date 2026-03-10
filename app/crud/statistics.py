"""
Statistics CRUD Operations
===========================
Queries for dashboard statistics and analytics.

SQL Learning Points:
- Aggregate functions: COUNT(), SUM(), AVG()
- Filtering with WHERE
- Joins across multiple tables
- Date filtering (CURRENT_DATE)
- Subqueries for complex aggregations
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.salary import Salary
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.user import User


class CRUDStatistics:
    """
    Statistics queries for dashboard and analytics.
    Each method demonstrates different SQL patterns.
    """
    
    def get_dashboard_metrics(self, db: Session) -> dict:
        """
        Get all dashboard metrics in a single response.
        
        SQL Learning: Multiple independent COUNT queries
        Performance: Could be optimized with subqueries or CTEs
        
        Returns:
            Dictionary with all dashboard metrics
        """
        today = date.today()
        first_day_of_month = today.replace(day=1)
        
        # ========== EMPLOYEES STATISTICS ==========
        # SQL: SELECT COUNT(*) FROM employees
        total_employees = db.query(func.count(Employee.id)).scalar() or 0
        
        # SQL: SELECT COUNT(*) FROM employees WHERE hire_date >= '2026-02-01'
        new_this_month = db.query(func.count(Employee.id))\
            .filter(Employee.hire_date >= first_day_of_month)\
            .scalar() or 0
        
        # Active employees - those with current salary (simplified: all employees)
        active_employees = total_employees
        
        # ========== DEPARTMENTS STATISTICS ==========
        # SQL: SELECT COUNT(*) FROM departments
        total_departments = db.query(func.count(Department.id)).scalar() or 0
        
        # Find largest department
        # SQL: SELECT d.id, d.name, COUNT(e.id) as emp_count
        #      FROM departments d
        #      LEFT JOIN employees e ON e.department_id = d.id
        #      GROUP BY d.id, d.name
        #      ORDER BY emp_count DESC
        #      LIMIT 1
        largest_dept = db.query(
            Department.name,
            func.count(Employee.id).label('emp_count')
        ).outerjoin(Employee, Employee.department_id == Department.id)\
         .group_by(Department.id, Department.name)\
         .order_by(func.count(Employee.id).desc())\
         .first()
        
        # Find smallest department (with at least 1 employee)
        smallest_dept = db.query(
            Department.name,
            func.count(Employee.id).label('emp_count')
        ).outerjoin(Employee, Employee.department_id == Department.id)\
         .group_by(Department.id, Department.name)\
         .having(func.count(Employee.id) > 0)\
         .order_by(func.count(Employee.id).asc())\
         .first()
        
        # ========== POSITIONS STATISTICS ==========
        # SQL: SELECT COUNT(*) FROM positions
        total_positions = db.query(func.count(Position.id)).scalar() or 0
        
        # Most common position
        # SQL: SELECT p.title, COUNT(e.id) as emp_count
        #      FROM positions p
        #      LEFT JOIN employees e ON e.position_id = p.id
        #      GROUP BY p.id, p.title
        #      ORDER BY emp_count DESC
        #      LIMIT 1
        most_common_position = db.query(
            Position.title,
            func.count(Employee.id).label('emp_count')
        ).outerjoin(Employee, Employee.position_id == Position.id)\
         .group_by(Position.id, Position.title)\
         .order_by(func.count(Employee.id).desc())\
         .first()
        
        # ========== ATTENDANCE TODAY ==========
        # SQL: SELECT status, COUNT(*) FROM attendances
        #      WHERE date = CURRENT_DATE
        #      GROUP BY status
        attendance_today = db.query(
            Attendance.status,
            func.count(Attendance.id).label('count')
        ).filter(Attendance.date == today)\
         .group_by(Attendance.status)\
         .all()
        
        # Convert to dictionary
        attendance_dict = {status: count for status, count in attendance_today}
        present_today = attendance_dict.get('present', 0)
        late_today = attendance_dict.get('late', 0)
        absent_today = attendance_dict.get('absent', 0)
        
        # Count employees on leave today
        # SQL: SELECT COUNT(*) FROM leaves
        #      WHERE status = 'approved'
        #      AND start_date <= CURRENT_DATE
        #      AND end_date >= CURRENT_DATE
        on_leave_today = db.query(func.count(Leave.id))\
            .filter(
                Leave.status == 'approved',
                Leave.start_date <= today,
                Leave.end_date >= today
            ).scalar() or 0
        
        # ========== LEAVES STATISTICS ==========
        # SQL: SELECT COUNT(*) FROM leaves WHERE status = 'pending'
        pending_leaves = db.query(func.count(Leave.id))\
            .filter(Leave.status == 'pending')\
            .scalar() or 0
        
        # Approved this month
        approved_this_month = db.query(func.count(Leave.id))\
            .filter(
                Leave.status == 'approved',
                Leave.start_date >= first_day_of_month
            ).scalar() or 0
        
        # ========== SALARIES STATISTICS ==========
        # SQL: SELECT SUM(base_salary), AVG(base_salary)
        #      FROM salaries
        #      WHERE effective_to IS NULL
        salary_stats = db.query(
            func.sum(Salary.base_salary).label('total'),
            func.avg(Salary.base_salary).label('average')
        ).filter(or_(Salary.effective_to == None, Salary.effective_to >= date.today()))\
         .first()
        
        total_payroll = float(salary_stats.total or 0)
        average_salary = float(salary_stats.average or 0)
        
        # Highest paid department by average salary
        # SQL: SELECT d.name, AVG(s.base_salary) as avg_sal
        #      FROM departments d
        #      INNER JOIN employees e ON e.department_id = d.id
        #      INNER JOIN salaries s ON s.employee_id = e.id
        #      WHERE s.effective_to IS NULL
        #      GROUP BY d.id, d.name
        #      ORDER BY avg_sal DESC
        #      LIMIT 1
        highest_paid_dept = db.query(
            Department.name,
            func.avg(Salary.base_salary).label('avg_salary')
        ).join(Employee, Employee.department_id == Department.id)\
         .join(Salary, Salary.employee_id == Employee.id)\
         .filter(or_(Salary.effective_to == None, Salary.effective_to >= date.today()))\
         .group_by(Department.id, Department.name)\
         .order_by(func.avg(Salary.base_salary).desc())\
         .first()
        
        # ========== USERS STATISTICS ==========
        # SQL: SELECT COUNT(*), role FROM users GROUP BY role
        user_counts = db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role)\
         .all()
        
        users_by_role = {role: count for role, count in user_counts}
        total_users = sum(users_by_role.values())
        
        # ========== BUILD RESPONSE ==========
        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "on_leave_today": on_leave_today,
                "new_this_month": new_this_month
            },
            "departments": {
                "total": total_departments,
                "largest": {
                    "name": largest_dept[0] if largest_dept else "N/A",
                    "employee_count": largest_dept[1] if largest_dept else 0
                },
                "smallest": {
                    "name": smallest_dept[0] if smallest_dept else "N/A",
                    "employee_count": smallest_dept[1] if smallest_dept else 0
                }
            },
            "positions": {
                "total": total_positions,
                "most_common": {
                    "title": most_common_position[0] if most_common_position else "N/A",
                    "count": most_common_position[1] if most_common_position else 0
                }
            },
            "attendance_today": {
                "date": today.isoformat(),
                "present": present_today,
                "late": late_today,
                "absent": absent_today,
                "on_leave": on_leave_today
            },
            "leaves": {
                "pending_requests": pending_leaves,
                "approved_this_month": approved_this_month
            },
            "salaries": {
                "total_payroll": round(total_payroll, 2),
                "average_salary": round(average_salary, 2),
                "highest_paid_department": highest_paid_dept[0] if highest_paid_dept else "N/A"
            },
            "users": {
                "total": total_users,
                "admins": users_by_role.get('admin', 0),
                "managers": users_by_role.get('manager', 0),
                "employees": users_by_role.get('employee', 0)
            }
        }


# Create global instance
statistics = CRUDStatistics()
