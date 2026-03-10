"""
Department API Router
=====================
Endpoints for managing departments.

Demonstrates:
  - GET /departments - list all
  - GET /departments/{id} - get one
  - POST /departments - create
  - PUT /departments/{id} - update
  - DELETE /departments/{id} - delete
  - GET /departments/search - advanced search (SQL: ILIKE, HAVING, dynamic ORDER BY)
  - POST /departments/compare - compare multiple departments (SQL: window functions, ranking)
  - GET /departments/{id}/employees - paginated employee list (SQL: OFFSET/LIMIT)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.crud import department as crud_department
from app.core.permissions import PermissionDependencies
from app.models.user import User

# Create router for department endpoints
router = APIRouter()


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all departments.
    
    Query Parameters:
      skip: Number of records to skip (default: 0)
      limit: Maximum records to return (default: 100)
      
    Returns:
      List of departments with id and name
    """
    departments = crud_department.get_multi(db, skip=skip, limit=limit)
    return departments


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_create_department)
):
    """
    Create a new department.
    Yêu cầu quyền CREATE_DEPARTMENT (Admin/Manager)
    
    Request Body:
      {
        "name": "Engineering"
      }
      
    Validation:
      - name must be unique
      - name is required
      
    Returns:
      The created department with auto-generated id
    """
    # Check if department with this name already exists
    # This prevents duplicate department names
    existing = crud_department.get_by_name(db, name=department_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{department_in.name}' already exists"
        )
    
    # Create and save the new department
    department = crud_department.create(db, obj_in=department_in)
    return department


# ============================================================================
# STATIC PATHS - THESE MUST COME BEFORE DYNAMIC PATHS /{department_id}
# ============================================================================

@router.get("/search")
def search_departments(
    name: Optional[str] = Query(None, description="Case-insensitive name search"),
    min_employees: Optional[int] = Query(None, description="Minimum employee count"),
    max_employees: Optional[int] = Query(None, description="Maximum employee count"),
    min_avg_salary: Optional[float] = Query(None, description="Minimum average salary"),
    max_avg_salary: Optional[float] = Query(None, description="Maximum average salary"),
    sort_by: str = Query("name", description="Sort field: name, employee_count, avg_salary"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, description="Pagination skip"),
    limit: int = Query(100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.authenticated_user)
):
    """
    Advanced department search with filters and sorting.
    
    SQL Learning Points:
    - ILIKE '%pattern%' for case-insensitive pattern matching
    - HAVING clause for filtering aggregated data (vs WHERE for raw data)
    - Dynamic ORDER BY based on request parameters
    - OFFSET/LIMIT for pagination
    - Multiple LEFT JOINs: departments → employees → salaries
    
    Query Parameters:
      name: Search in department name (case-insensitive)
      min_employees: Filter departments with at least N employees
      max_employees: Filter departments with at most N employees
      min_avg_salary: Filter departments with average salary >= N
      max_avg_salary: Filter departments with average salary <= N
      sort_by: Sort by 'name', 'employee_count', or 'avg_salary'
      order: 'asc' (ascending) or 'desc' (descending)
      skip: Number of records to skip (for pagination)
      limit: Maximum records to return
      
    Example Queries:
      - Search by name:
        GET /departments/search?name=eng
        
      - Filter by size:
        GET /departments/search?min_employees=10&max_employees=50
        
      - Filter by salary:
        GET /departments/search?min_avg_salary=40000000
        
      - Combined filters with sorting:
        GET /departments/search?name=eng&sort_by=employee_count&order=desc
        
      - Pagination:
        GET /departments/search?skip=0&limit=10  (page 1)
        GET /departments/search?skip=10&limit=10 (page 2)
    
    Returns:
      List of departments matching filters with employee count and average salary
      
    Example Response:
    [
      {
        "id": 1,
        "name": "Engineering",
        "employee_count": 25,
        "avg_salary": 50000000.0
      }
    ]
    """
    results = crud_department.search_departments(
        db=db,
        name=name,
        min_employees=min_employees,
        max_employees=max_employees,
        min_avg_salary=min_avg_salary,
        max_avg_salary=max_avg_salary,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit
    )
    
    # Hide salary data for Employee role
    from app.models.user import UserRole
    if current_user.role == UserRole.EMPLOYEE:
        for dept in results:
            if "avg_salary" in dept:
                dept["avg_salary"] = None
    
    return results


@router.post("/compare")
def compare_departments(
    department_ids: List[int],
    db: Session = Depends(get_db),
    _: User = Depends(PermissionDependencies.admin_or_manager)
):
    """
    Compare multiple departments side-by-side.
    
    SQL Learning Points:
    - Window Functions: ROW_NUMBER(), RANK()
    - PARTITION BY for grouping in window functions
    - Multiple aggregations in single query
    - WHERE IN clause for multiple IDs
    - Subqueries for complex calculations
    
    Request Body:
      [1, 2, 3, 4]  // List of department IDs to compare
      
    Returns:
      Detailed comparison with rankings by size and salary
      
    Example Response:
    {
      "comparison": [
        {
          "department_id": 1,
          "department_name": "Engineering",
          "total_employees": 25,
          "total_salary_budget": 1250000000.0,
          "avg_salary": 50000000.0,
          "unique_positions": 5,
          "rank_by_size": 1,       // 1st largest
          "rank_by_salary": 2      // 2nd highest paid
        },
        {
          "department_id": 2,
          "department_name": "Sales",
          "total_employees": 20,
          "total_salary_budget": 1000000000.0,
          "avg_salary": 50000000.0,
          "unique_positions": 3,
          "rank_by_size": 2,
          "rank_by_salary": 2
        }
      ],
      "summary": {
        "largest_department": "Engineering",
        "highest_paid_department": "Marketing",
        "most_diverse_positions": "Engineering"
      }
    }
    
    Use Cases:
    - Compare department efficiencies
    - Identify resource allocation patterns
    - Find departments needing attention
    """
    if not department_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng cung cấp danh sách department IDs"
        )
    
    result = crud_department.compare_departments(db, department_ids=department_ids)
    
    if not result["comparison"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phòng ban nào với các IDs đã cung cấp"
        )
    
    return result


@router.get("/list/with-counts")
def list_departments_with_counts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(PermissionDependencies.authenticated_user)
):
    """
    Get all departments with employee counts.
    
    Useful for displaying department overview with sizes.
    
    SQL Learning: LEFT JOIN, COUNT, GROUP BY
    
    Query Parameters:
      skip: Number of records to skip (default: 0)
      limit: Maximum records to return (default: 100)
    
    Returns:
      List of departments with employee_count field
      
    Example Response:
    [
      {
        "id": 1,
        "name": "Engineering",
        "employee_count": 25
      },
      {
        "id": 2,
        "name": "Sales",
        "employee_count": 20
      }
    ]
    """
    departments = crud_department.get_with_employee_count(db, skip=skip, limit=limit)
    return departments


# ============================================================================
# DYNAMIC PATHS - THESE MUST COME AFTER STATIC PATHS
# ============================================================================

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single department by ID.
    
    Path Parameters:
      department_id: The department's primary key
      
    Returns:
      Department data or 404 if not found
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_update_department)
):
    """
    Update a department.
    Yêu cầu quyền UPDATE_DEPARTMENT (Admin/Manager)
    
    Path Parameters:
      department_id: The department's primary key
      
    Request Body (all optional):
      {
        "name": "New Department Name"
      }
      
    Returns:
      Updated department data or 404 if not found
    """
    department = crud_department.get(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    
    # If new name provided, check for duplicates
    if department_in.name and department_in.name != department.name:
        existing = crud_department.get_by_name(db, name=department_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with name '{department_in.name}' already exists"
            )
    
    # Update and save
    department = crud_department.update(db, db_obj=department, obj_in=department_in)
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_delete_department)
):
    """
    Delete a department by ID.
    Yêu cầu quyền DELETE_DEPARTMENT (Admin only)
    
    Path Parameters:
      department_id: The department's primary key
      
    Returns:
      No content (204) on successful deletion or 404 if not found
      
    Note:
      Deleting a department will cascade-delete all employees in it
      (due to cascade="all, delete-orphan" in the model)
    """
    department = crud_department.delete(db, id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    # 204 responses don't have a body, so we just return


@router.get("/{department_id}/statistics")
def get_department_statistics(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(PermissionDependencies.admin_or_manager)
):
    """
    Get comprehensive statistics for a department.
    
    Returns:
      - Total employees in department
      - Employee breakdown by position
      - Salary statistics (total budget, avg, min, max)
      - Newest employee (most recent hire)
      - Longest-serving employee
    
    SQL Learning Points:
      - LEFT JOIN with conditions
      - Multiple aggregates (COUNT, SUM, AVG, MIN, MAX)
      - GROUP BY with HAVING
      - ORDER BY with LIMIT for top/bottom records
    
    Example Response:
    {
      "department_id": 1,
      "department_name": "Engineering",
      "total_employees": 25,
      "employee_breakdown_by_position": [
        {
          "position_id": 1,
          "position_title": "Software Engineer",
          "count": 15
        }
      ],
      "salary_stats": {
        "total_salary_budget": 1250000000.0,
        "average_salary": 50000000.0,
        "min_salary": 15000000.0,
        "max_salary": 80000000.0
      },
      "newest_employee": {
        "id": 42,
        "name": "Nguyen Van A",
        "hire_date": "2026-02-10"
      },
      "longest_serving_employee": {
        "id": 5,
        "name": "Tran Thi B",
        "hire_date": "2020-01-15"
      }
    }
    """
    statistics = crud_department.get_department_statistics(db, department_id)
    if not statistics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {department_id} not found"
        )
    return statistics


@router.get("/{department_id}/employees")
def get_department_employees(
    department_id: int,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page"),
    sort_by: str = Query("name", description="Sort field: name, hire_date, salary"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    position_id: Optional[int] = Query(None, description="Filter by position ID"),
    db: Session = Depends(get_db),
    _: User = Depends(PermissionDependencies.admin_or_manager)
):
    """
    Get employees of a department with pagination.
    
    SQL Learning Points:
    - OFFSET and LIMIT for pagination
    - Pagination formula: OFFSET = (page - 1) * page_size
    - Multiple JOINs: employees → departments, positions, salaries
    - Dynamic WHERE conditions (optional filters)
    - COUNT(*) for total records (requires separate query or window function)
    
    Path Parameters:
      department_id: The department to list employees from
      
    Query Parameters:
      page: Page number (1, 2, 3, ...)
      page_size: Number of records per page (1-100)
      sort_by: Sort by 'name', 'hire_date', or 'salary'
      order: 'asc' or 'desc'
      position_id: Optional filter by position
      
    Pagination Examples:
      - Page 1, 10 per page: OFFSET 0 LIMIT 10  (records 1-10)
      - Page 2, 10 per page: OFFSET 10 LIMIT 10 (records 11-20)
      - Page 3, 10 per page: OFFSET 20 LIMIT 10 (records 21-30)
      
    Example Queries:
      - First page:
        GET /departments/1/employees?page=1&page_size=10
        
      - Sort by hire date (newest first):
        GET /departments/1/employees?sort_by=hire_date&order=desc
        
      - Filter by position and sort by salary:
        GET /departments/1/employees?position_id=5&sort_by=salary&order=desc
    
    Returns:
      Paginated employee list with metadata
      
    Example Response:
    {
      "department_id": 1,
      "department_name": "Engineering",
      "pagination": {
        "page": 1,
        "page_size": 10,
        "total_records": 25,
        "total_pages": 3
      },
      "employees": [
        {
          "id": 1,
          "name": "Nguyen Van A",
          "email": "a@example.com",
          "position": "Software Engineer",
          "hire_date": "2022-01-15",
          "current_salary": 50000000.0
        }
      ]
    }
    """
    result = crud_department.get_department_employees(
        db=db,
        department_id=department_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
        position_id=position_id
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phòng ban với ID {department_id} không tồn tại"
        )
    
    return result
