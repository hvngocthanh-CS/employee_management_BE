from typing import Optional
from datetime import datetime


def generate_employee_code(prefix: str = "EMP") -> str:
    """Generate a unique employee code."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{timestamp}"


def calculate_leave_days(start_date: datetime, end_date: datetime) -> int:
    """Calculate total days between start and end date (inclusive)."""
    delta = end_date - start_date
    return delta.days + 1


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to string."""
    if dt is None:
        return None
    return dt.isoformat()
