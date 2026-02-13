"""
Permission System
=================
Role-based access control for Employee Management System
"""

from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_current_user, get_db
from app.models.user import User, UserRole


class Permission(str, Enum):
    """Available permissions in the system"""
    
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Employee Management
    CREATE_EMPLOYEE = "create_employee"
    READ_EMPLOYEE = "read_employee"
    UPDATE_EMPLOYEE = "update_employee"
    DELETE_EMPLOYEE = "delete_employee"
    READ_OWN_EMPLOYEE_DATA = "read_own_employee_data"
    
    # Department Management
    CREATE_DEPARTMENT = "create_department"
    READ_DEPARTMENT = "read_department"
    UPDATE_DEPARTMENT = "update_department"
    DELETE_DEPARTMENT = "delete_department"
    
    # Position Management
    CREATE_POSITION = "create_position"
    READ_POSITION = "read_position"
    UPDATE_POSITION = "update_position"
    DELETE_POSITION = "delete_position"
    
    # Salary Management
    CREATE_SALARY = "create_salary"
    READ_SALARY = "read_salary"
    UPDATE_SALARY = "update_salary"
    DELETE_SALARY = "delete_salary"
    READ_OWN_SALARY = "read_own_salary"
    
    # Attendance Management
    CREATE_ATTENDANCE = "create_attendance"
    READ_ATTENDANCE = "read_attendance"
    UPDATE_ATTENDANCE = "update_attendance"
    DELETE_ATTENDANCE = "delete_attendance"
    READ_OWN_ATTENDANCE = "read_own_attendance"
    MARK_OWN_ATTENDANCE = "mark_own_attendance"
    
    # Leave Management
    CREATE_LEAVE = "create_leave"
    READ_LEAVE = "read_leave"
    UPDATE_LEAVE = "update_leave"
    DELETE_LEAVE = "delete_leave"
    APPROVE_LEAVE = "approve_leave"
    READ_OWN_LEAVE = "read_own_leave"
    REQUEST_OWN_LEAVE = "request_own_leave"
    

# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        # Admin has all permissions
        Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
        Permission.CREATE_EMPLOYEE, Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE, Permission.DELETE_EMPLOYEE,
        Permission.CREATE_DEPARTMENT, Permission.READ_DEPARTMENT, Permission.UPDATE_DEPARTMENT, Permission.DELETE_DEPARTMENT,
        Permission.CREATE_POSITION, Permission.READ_POSITION, Permission.UPDATE_POSITION, Permission.DELETE_POSITION,
        Permission.CREATE_SALARY, Permission.READ_SALARY, Permission.UPDATE_SALARY, Permission.DELETE_SALARY,
        Permission.CREATE_ATTENDANCE, Permission.READ_ATTENDANCE, Permission.UPDATE_ATTENDANCE, Permission.DELETE_ATTENDANCE,
        Permission.CREATE_LEAVE, Permission.READ_LEAVE, Permission.UPDATE_LEAVE, Permission.DELETE_LEAVE, Permission.APPROVE_LEAVE,
    ],
    
    UserRole.MANAGER: [
        # Manager can manage employees, departments, positions, and approve leaves
        Permission.READ_USER,
        Permission.CREATE_EMPLOYEE, Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE,
        Permission.CREATE_DEPARTMENT, Permission.READ_DEPARTMENT, Permission.UPDATE_DEPARTMENT,
        Permission.CREATE_POSITION, Permission.READ_POSITION, Permission.UPDATE_POSITION,
        Permission.CREATE_SALARY, Permission.READ_SALARY, Permission.UPDATE_SALARY,
        Permission.READ_ATTENDANCE, Permission.UPDATE_ATTENDANCE,
        Permission.READ_LEAVE, Permission.UPDATE_LEAVE, Permission.APPROVE_LEAVE,
        # Own data access
        Permission.READ_OWN_EMPLOYEE_DATA, Permission.READ_OWN_SALARY, 
        Permission.READ_OWN_ATTENDANCE, Permission.MARK_OWN_ATTENDANCE,
        Permission.READ_OWN_LEAVE, Permission.REQUEST_OWN_LEAVE,
    ],
    
    UserRole.EMPLOYEE: [
        # Employee can only access their own data and basic read operations
        Permission.READ_DEPARTMENT, Permission.READ_POSITION,
        # Own data access only
        Permission.READ_OWN_EMPLOYEE_DATA, Permission.READ_OWN_SALARY,
        Permission.READ_OWN_ATTENDANCE, Permission.MARK_OWN_ATTENDANCE,
        Permission.READ_OWN_LEAVE, Permission.REQUEST_OWN_LEAVE,
    ]
}


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has specific permission"""
    if not user.is_active:
        return False
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def require_permission(permission: Permission):
    """Dependency to require specific permission"""
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    
    return permission_dependency


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles"""
    def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_dependency


def require_own_resource_or_permission(permission: Permission):
    """
    Dependency for resources that can be accessed by owner or users with permission
    Use this for endpoints where users can access their own data or admins/managers can access any
    """
    def own_resource_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # If user has the general permission, allow access
        if has_permission(current_user, permission):
            return current_user
        
        # For employee-level access, we'll check ownership in the endpoint logic
        # This dependency just ensures user is authenticated
        return current_user
    
    return own_resource_dependency


# Convenience dependencies for common permission checks
class PermissionDependencies:
    """Common permission dependencies"""
    
    # Admin only
    admin_only = require_role([UserRole.ADMIN])
    
    # Admin and Manager
    admin_or_manager = require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    # User Management
    can_create_user = require_permission(Permission.CREATE_USER)
    can_read_user = require_permission(Permission.READ_USER)
    can_update_user = require_permission(Permission.UPDATE_USER)
    can_delete_user = require_permission(Permission.DELETE_USER)
    
    # Employee Management
    can_create_employee = require_permission(Permission.CREATE_EMPLOYEE)
    can_read_employee = require_permission(Permission.READ_EMPLOYEE)
    can_update_employee = require_permission(Permission.UPDATE_EMPLOYEE)
    can_delete_employee = require_permission(Permission.DELETE_EMPLOYEE)
    can_read_own_employee_data = require_own_resource_or_permission(Permission.READ_EMPLOYEE)
    
    # Department Management
    can_create_department = require_permission(Permission.CREATE_DEPARTMENT)
    can_read_department = require_permission(Permission.READ_DEPARTMENT)
    can_update_department = require_permission(Permission.UPDATE_DEPARTMENT)
    can_delete_department = require_permission(Permission.DELETE_DEPARTMENT)
    
    # Position Management
    can_create_position = require_permission(Permission.CREATE_POSITION)
    can_read_position = require_permission(Permission.READ_POSITION)
    can_update_position = require_permission(Permission.UPDATE_POSITION)
    can_delete_position = require_permission(Permission.DELETE_POSITION)
    
    # Salary Management
    can_create_salary = require_permission(Permission.CREATE_SALARY)
    can_read_salary = require_permission(Permission.READ_SALARY)
    can_update_salary = require_permission(Permission.UPDATE_SALARY)
    can_delete_salary = require_permission(Permission.DELETE_SALARY)
    can_read_own_salary = require_own_resource_or_permission(Permission.READ_SALARY)
    
    # Attendance Management
    can_create_attendance = require_permission(Permission.CREATE_ATTENDANCE)
    can_read_attendance = require_permission(Permission.READ_ATTENDANCE)
    can_update_attendance = require_permission(Permission.UPDATE_ATTENDANCE)
    can_delete_attendance = require_permission(Permission.DELETE_ATTENDANCE)
    can_read_own_attendance = require_own_resource_or_permission(Permission.READ_ATTENDANCE)
    can_mark_own_attendance = require_permission(Permission.MARK_OWN_ATTENDANCE)
    
    # Leave Management
    can_create_leave = require_permission(Permission.CREATE_LEAVE)
    can_read_leave = require_permission(Permission.READ_LEAVE)
    can_update_leave = require_permission(Permission.UPDATE_LEAVE)
    can_delete_leave = require_permission(Permission.DELETE_LEAVE)
    can_approve_leave = require_permission(Permission.APPROVE_LEAVE)
    can_read_own_leave = require_own_resource_or_permission(Permission.READ_LEAVE)


def check_resource_ownership(user: User, resource_employee_id: Optional[int]) -> bool:
    """Check if user owns the resource (for employee-level users)"""
    if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        return True  # Admin and Manager can access any resource
    
    # For employees, check if the resource belongs to them
    return user.employee_id == resource_employee_id


def get_user_permissions(user: User) -> List[str]:
    """Get list of permissions for a user"""
    if not user.is_active:
        return []
    
    permissions = ROLE_PERMISSIONS.get(user.role, [])
    return [perm.value for perm in permissions]


def get_menu_permissions(user: User) -> dict:
    """Get menu visibility permissions for frontend"""
    permissions = get_user_permissions(user)
    
    return {
        "dashboard": True,  # Everyone can see dashboard
        "employees": Permission.READ_EMPLOYEE.value in permissions or Permission.READ_OWN_EMPLOYEE_DATA.value in permissions,
        "users": Permission.READ_USER.value in permissions,
        "departments": Permission.READ_DEPARTMENT.value in permissions,
        "positions": Permission.READ_POSITION.value in permissions,
        "salaries": Permission.READ_SALARY.value in permissions or Permission.READ_OWN_SALARY.value in permissions,
        "attendances": Permission.READ_ATTENDANCE.value in permissions or Permission.READ_OWN_ATTENDANCE.value in permissions,
        "leaves": Permission.READ_LEAVE.value in permissions or Permission.READ_OWN_LEAVE.value in permissions,
        
        # Action permissions
        "can_create_employee": Permission.CREATE_EMPLOYEE.value in permissions,
        "can_edit_employee": Permission.UPDATE_EMPLOYEE.value in permissions,
        "can_delete_employee": Permission.DELETE_EMPLOYEE.value in permissions,
        "can_approve_leave": Permission.APPROVE_LEAVE.value in permissions,
        "can_manage_departments": Permission.UPDATE_DEPARTMENT.value in permissions,
        "can_manage_positions": Permission.UPDATE_POSITION.value in permissions,
    }