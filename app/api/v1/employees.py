from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import Employee

router = APIRouter()


@router.get("/")
def list_employees(db: Session = Depends(get_db)):
    """
    List all employees - đơn giản cho WPF
    """
    employees = db.query(Employee).all()
    return {"data": [{
        "id": e.id,
        "first_name": e.first_name,
        "last_name": e.last_name,
        "email": e.email,
        "phone": e.phone
    } for e in employees], "total": len(employees)}


@router.post("/")
def create_employee(employee_in: dict, db: Session = Depends(get_db)):
    """
    Create employee - đơn giản cho WPF
    """
    new_employee = Employee(
        first_name=employee_in.get("first_name"),
        last_name=employee_in.get("last_name"),
        email=employee_in.get("email"),
        phone=employee_in.get("phone", "")
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return {
        "message": "Employee created successfully",
        "id": new_employee.id,
        "first_name": new_employee.first_name,
        "last_name": new_employee.last_name,
        "email": new_employee.email
    }