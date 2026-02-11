from app.crud.department import department
from app.crud.position import position
from app.crud.employee import employee
from app.crud.user import user
from app.crud.salary import salary
from app.crud.attendance import attendance
from app.crud.leave import leave

# Export all CRUD instances
__all__ = [
    "department",
    "position",
    "employee", 
    "user",
    "salary",
    "attendance",
    "leave"
]