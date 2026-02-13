"""
API v1 Router
=============
Combines all v1 API routers
"""

from fastapi import APIRouter
from app.api.v1 import (
    auth,
    departments,
    employees,
    positions,
    user,
    salaries,
    attendances,
    leaves
)

# Create main router for API v1
api_router = APIRouter()

# Include all routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    departments.router,
    prefix="/departments",
    tags=["Departments"]
)

api_router.include_router(
    positions.router,
    prefix="/positions",
    tags=["Positions"]
)

api_router.include_router(
    employees.router,
    prefix="/employees",
    tags=["Employees"]
)

api_router.include_router(
    user.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    salaries.router,
    prefix="/salaries",
    tags=["Salaries"]
)

api_router.include_router(
    attendances.router,
    prefix="/attendances",
    tags=["Attendances"]
)

api_router.include_router(
    leaves.router,
    prefix="/leaves",
    tags=["Leaves"]
)
