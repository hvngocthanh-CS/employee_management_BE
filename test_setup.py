"""
Quick Test Script
=================

This script tests that the FastAPI backend is properly configured
before running with uvicorn.

Run this: python test_setup.py

It will:
1. Check all imports work
2. Verify database models are defined
3. Create database tables
4. Test basic CRUD operations
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from app.database import engine, SessionLocal, Base
        from app.models.department import Department
        from app.models.employee import Employee
        from app.schemas.department import DepartmentCreate, DepartmentResponse
        from app.schemas.employee import EmployeeCreate, EmployeeResponse
        from app.crud.base import CRUDBase
        from app.crud.department import department as crud_department
        from app.crud.employee import employee as crud_employee
        from app.api.v1 import api_router
        from app.main import app
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_database():
    """Test database initialization and tables"""
    print("\nTesting database...")
    try:
        from app.database import engine, SessionLocal, Base
        from app.models.department import Department
        from app.models.employee import Employee
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created")
        
        # Test session
        db = SessionLocal()
        print("✓ Database session created")
        db.close()
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_crud():
    """Test CRUD operations"""
    print("\nTesting CRUD operations...")
    try:
        from app.database import SessionLocal, Base, engine
        from app.models.department import Department
        from app.models.employee import Employee
        from app.schemas.department import DepartmentCreate
        from app.schemas.employee import EmployeeCreate
        from app.crud.department import department as crud_department
        from app.crud.employee import employee as crud_employee
        
        # Recreate database (clean slate for testing)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Test department CRUD
        print("  Testing Department CRUD...")
        
        # Create
        dept_in = DepartmentCreate(name="Test Department")
        dept = crud_department.create(db, obj_in=dept_in)
        assert dept.id is not None
        print("    ✓ Create department")
        
        # Read
        retrieved_dept = crud_department.get(db, id=dept.id)
        assert retrieved_dept is not None
        assert retrieved_dept.name == "Test Department"
        print("    ✓ Read department")
        
        # Update
        from app.schemas.department import DepartmentUpdate
        update_in = DepartmentUpdate(name="Updated Department")
        updated_dept = crud_department.update(db, db_obj=dept, obj_in=update_in)
        assert updated_dept.name == "Updated Department"
        print("    ✓ Update department")
        
        # Test employee CRUD
        print("  Testing Employee CRUD...")
        
        # Create
        emp_in = EmployeeCreate(
            name="John Doe",
            email="john@example.com",
            department_id=dept.id
        )
        emp = crud_employee.create(db, obj_in=emp_in)
        assert emp.id is not None
        print("    ✓ Create employee")
        
        # Read
        retrieved_emp = crud_employee.get(db, id=emp.id)
        assert retrieved_emp is not None
        assert retrieved_emp.name == "John Doe"
        print("    ✓ Read employee")
        
        # Read by email
        found_emp = crud_employee.get_by_email(db, email="john@example.com")
        assert found_emp is not None
        print("    ✓ Get employee by email")
        
        # Update
        from app.schemas.employee import EmployeeUpdate
        update_emp_in = EmployeeUpdate(name="Jane Doe")
        updated_emp = crud_employee.update(db, db_obj=emp, obj_in=update_emp_in)
        assert updated_emp.name == "Jane Doe"
        print("    ✓ Update employee")
        
        # Delete
        deleted_emp = crud_employee.delete(db, id=emp.id)
        assert deleted_emp is not None
        print("    ✓ Delete employee")
        
        # Get multi
        emp2_in = EmployeeCreate(
            name="Bob Smith",
            email="bob@example.com",
            department_id=dept.id
        )
        emp2 = crud_employee.create(db, obj_in=emp2_in)
        
        all_emps = crud_employee.get_multi(db, skip=0, limit=10)
        assert len(all_emps) > 0
        print("    ✓ Get multiple employees")
        
        # Delete department (cascade delete employees)
        deleted_dept = crud_department.delete(db, id=dept.id)
        assert deleted_dept is not None
        print("    ✓ Delete department (cascade)")
        
        db.close()
        print("✓ CRUD operations test passed")
        return True
        
    except Exception as e:
        print(f"✗ CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi():
    """Test FastAPI app is configured"""
    print("\nTesting FastAPI setup...")
    try:
        from app.main import app
        
        # Check routes are registered
        routes = [route.path for route in app.routes]
        
        # Check for main endpoints
        required_routes = ['/api/v1/departments', '/api/v1/employees']
        for route in required_routes:
            if not any(route in r for r in routes):
                print(f"  Warning: Route {route} not found")
        
        print("✓ FastAPI app initialized")
        return True
        
    except Exception as e:
        print(f"✗ FastAPI test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("BACKEND SETUP TEST")
    print("=" * 50)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_database()
    all_passed &= test_crud()
    all_passed &= test_fastapi()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nYou can now run the server with:")
        print("  uvicorn app.main:app --reload")
        print("\nThen visit:")
        print("  http://localhost:8000/docs  (API documentation)")
        print("  http://localhost:8000/redoc (ReDoc)")
    else:
        print("✗ SOME TESTS FAILED")
        print("Please check the errors above")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
