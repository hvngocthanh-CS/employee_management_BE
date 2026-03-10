"""
Statistics API Router
=====================
Endpoints for dashboard statistics and analytics.

Demonstrates:
  - GET /statistics/dashboard - All dashboard metrics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import statistics as crud_statistics
from app.core.deps import get_current_user
from app.models.user import User, UserRole

# Create router for statistics endpoints
router = APIRouter()


@router.get("/dashboard")
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all dashboard statistics in a single response.
    
    Permissions:
      - Admin/Manager: Full statistics including salary data
      - Employee: Limited statistics (no salary data)
    
    Returns comprehensive metrics including:
    - Employee counts (total, active, new, on leave)
    - Department statistics (total, largest, smallest)
    - Position statistics (total, most common)
    - Attendance today (present, late, absent, on leave)
    - Leave requests (pending, approved this month)
    - Salary statistics (Admin/Manager only)
    - User counts by role (Admin/Manager only)
    """
    metrics = crud_statistics.statistics.get_dashboard_metrics(db)
    
    # For Employee role, hide sensitive data
    if current_user.role == UserRole.EMPLOYEE:
        # Hide salary statistics
        metrics["salaries"] = {
            "total_payroll": None,
            "average_salary": None,
            "highest_paid_department": None
        }
        # Hide user counts
        metrics["users"] = {
            "total": None,
            "admins": None,
            "managers": None,
            "employees": None
        }
    
    return metrics
    """
    Get all dashboard statistics in a single response.
    
    Returns comprehensive metrics including:
    - Employee counts (total, active, new, on leave)
    - Department statistics (total, largest, smallest)
    - Position statistics (total, most common)
    - Attendance today (present, late, absent, on leave)
    - Leave requests (pending, approved this month)
    - Salary statistics (total payroll, average, highest paid dept)
    - User counts by role (admin, manager, employee)
    
    SQL Learning Points:
    - Multiple aggregate queries (COUNT, SUM, AVG)
    - GROUP BY with multiple tables
    - LEFT JOIN for optional relationships
    - HAVING clause for filtered groups
    - Date filtering (today, this month)
    - Subqueries for rankings
    
    Example Response:
    {
      "employees": {
        "total": 67,
        "active": 65,
        "on_leave_today": 2,
        "new_this_month": 5
      },
      "departments": {
        "total": 6,
        "largest": {
          "name": "Engineering",
          "employee_count": 25
        },
        "smallest": {
          "name": "Operations",
          "employee_count": 5
        }
      },
      "positions": {
        "total": 10,
        "most_common": {
          "title": "Software Engineer",
          "count": 15
        }
      },
      "attendance_today": {
        "date": "2026-02-21",
        "present": 45,
        "late": 3,
        "absent": 17,
        "on_leave": 2
      },
      "leaves": {
        "pending_requests": 2,
        "approved_this_month": 8
      },
      "salaries": {
        "total_payroll": 3350000000.0,
        "average_salary": 50000000.0,
        "highest_paid_department": "Engineering"
      },
      "users": {
        "total": 12,
        "admins": 2,
        "managers": 4,
        "employees": 6
      }
    }
    """
    metrics = crud_statistics.statistics.get_dashboard_metrics(db)
    return metrics
