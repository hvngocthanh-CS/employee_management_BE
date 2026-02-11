from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import date, datetime
from app.crud.base import CRUDBase
from app.models.leave import Leave, LeaveType, LeaveStatus
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.leave import LeaveCreate, LeaveUpdate


class CRUDLeave(CRUDBase[Leave, LeaveCreate, LeaveUpdate]):
    """CRUD operations cho Leave với advanced queries"""
    
    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        status: Optional[LeaveStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Leave]:
        """Get leave requests của một nhân viên"""
        query = db.query(Leave).filter(Leave.employee_id == employee_id)
        
        if status:
            query = query.filter(Leave.status == status)
        
        return query.order_by(Leave.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_pending_leaves(
        self,
        db: Session,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Leave]:
        """Get tất cả leave requests đang chờ duyệt"""
        query = db.query(Leave)\
            .filter(Leave.status == LeaveStatus.PENDING)
        
        if department_id:
            query = query.join(Employee, Leave.employee_id == Employee.id)\
                .filter(Employee.department_id == department_id)
        
        return query.order_by(Leave.created_at.asc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_leaves_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        department_id: Optional[int] = None,
        status: Optional[LeaveStatus] = None
    ) -> List[Leave]:
        """
        Get leaves trong khoảng thời gian
        Bao gồm cả leaves overlap với khoảng thời gian
        """
        query = db.query(Leave)\
            .filter(
                or_(
                    # Leave starts trong range
                    and_(
                        Leave.start_date >= start_date,
                        Leave.start_date <= end_date
                    ),
                    # Leave ends trong range
                    and_(
                        Leave.end_date >= start_date,
                        Leave.end_date <= end_date
                    ),
                    # Leave spans across range
                    and_(
                        Leave.start_date <= start_date,
                        Leave.end_date >= end_date
                    )
                )
            )
        
        if department_id:
            query = query.join(Employee, Leave.employee_id == Employee.id)\
                .filter(Employee.department_id == department_id)
        
        if status:
            query = query.filter(Leave.status == status)
        
        return query.all()
    
    def approve_leave(
        self,
        db: Session,
        leave_id: int,
        approver_id: int
    ) -> Leave:
        """Duyệt đơn nghỉ phép"""
        leave = self.get(db, id=leave_id)
        if not leave:
            raise ValueError("Leave not found")
        
        if leave.status != LeaveStatus.PENDING:
            raise ValueError(f"Cannot approve leave with status: {leave.status}")
        
        leave.status = LeaveStatus.APPROVED
        leave.approved_by = approver_id
        leave.approved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(leave)
        
        return leave
    
    def reject_leave(
        self,
        db: Session,
        leave_id: int,
        approver_id: int
    ) -> Leave:
        """Từ chối đơn nghỉ phép"""
        leave = self.get(db, id=leave_id)
        if not leave:
            raise ValueError("Leave not found")
        
        if leave.status != LeaveStatus.PENDING:
            raise ValueError(f"Cannot reject leave with status: {leave.status}")
        
        leave.status = LeaveStatus.REJECTED
        leave.approved_by = approver_id
        leave.approved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(leave)
        
        return leave
    
    def cancel_leave(
        self,
        db: Session,
        leave_id: int,
        employee_id: int
    ) -> Leave:
        """Hủy đơn nghỉ phép (chỉ được hủy nếu pending hoặc approved)"""
        leave = self.get(db, id=leave_id)
        if not leave:
            raise ValueError("Leave not found")
        
        if leave.employee_id != employee_id:
            raise ValueError("You can only cancel your own leave")
        
        if leave.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
            raise ValueError(f"Cannot cancel leave with status: {leave.status}")
        
        # Không được hủy nếu leave đã bắt đầu
        if leave.start_date < date.today():
            raise ValueError("Cannot cancel leave that has already started")
        
        leave.status = LeaveStatus.CANCELLED
        db.commit()
        db.refresh(leave)
        
        return leave
    
    def check_leave_conflict(
        self,
        db: Session,
        employee_id: int,
        start_date: date,
        end_date: date,
        exclude_leave_id: Optional[int] = None
    ) -> bool:
        """
        Check xem có leave nào conflict không
        Returns True nếu có conflict
        """
        query = db.query(Leave)\
            .filter(
                and_(
                    Leave.employee_id == employee_id,
                    Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                    or_(
                        and_(
                            Leave.start_date <= end_date,
                            Leave.end_date >= start_date
                        )
                    )
                )
            )
        
        if exclude_leave_id:
            query = query.filter(Leave.id != exclude_leave_id)
        
        return query.count() > 0
    
    def get_leave_balance(
        self,
        db: Session,
        employee_id: int,
        year: int
    ) -> dict:
        """
        Tính số ngày phép còn lại trong năm
        """
        # Tổng số ngày phép năm (giả sử 12 ngày)
        total_annual = 12
        
        # Đếm số ngày đã sử dụng (approved leaves trong năm)
        used = db.query(func.sum(Leave.total_days))\
            .filter(
                and_(
                    Leave.employee_id == employee_id,
                    Leave.leave_type == LeaveType.ANNUAL,
                    Leave.status == LeaveStatus.APPROVED,
                    extract('year', Leave.start_date) == year
                )
            )\
            .scalar() or 0
        
        # Đếm số ngày pending
        pending = db.query(func.sum(Leave.total_days))\
            .filter(
                and_(
                    Leave.employee_id == employee_id,
                    Leave.leave_type == LeaveType.ANNUAL,
                    Leave.status == LeaveStatus.PENDING,
                    extract('year', Leave.start_date) == year
                )
            )\
            .scalar() or 0
        
        return {
            "employee_id": employee_id,
            "year": year,
            "total_annual_leave": total_annual,
            "used_annual_leave": int(used),
            "pending_leave": int(pending),
            "remaining_annual_leave": total_annual - int(used)
        }
    
    def get_leave_statistics(
        self,
        db: Session,
        month: int,
        year: int,
        department_id: Optional[int] = None
    ) -> dict:
        """Thống kê nghỉ phép theo tháng"""
        query = db.query(Leave)\
            .filter(
                and_(
                    extract('month', Leave.start_date) == month,
                    extract('year', Leave.start_date) == year
                )
            )
        
        if department_id:
            query = query.join(Employee, Leave.employee_id == Employee.id)\
                .filter(Employee.department_id == department_id)
        
        leaves = query.all()
        
        # Statistics by type
        by_type = {}
        for leave_type in LeaveType:
            count = sum(1 for l in leaves if l.leave_type == leave_type)
            by_type[leave_type.value] = count
        
        # Statistics by status
        by_status = {}
        for status in LeaveStatus:
            count = sum(1 for l in leaves if l.status == status)
            by_status[status.value] = count
        
        # Statistics by department
        by_dept = {}
        for leave in leaves:
            if leave.employee and leave.employee.department:
                dept_name = leave.employee.department.name
                by_dept[dept_name] = by_dept.get(dept_name, 0) + 1
        
        return {
            "month": month,
            "year": year,
            "total_leaves": len(leaves),
            "by_type": by_type,
            "by_status": by_status,
            "by_department": by_dept
        }
    
    def get_leave_calendar(
        self,
        db: Session,
        target_date: date,
        department_id: Optional[int] = None
    ) -> dict:
        """Lịch nghỉ phép trong một ngày"""
        leaves = self.get_leaves_by_date_range(
            db,
            start_date=target_date,
            end_date=target_date,
            department_id=department_id,
            status=LeaveStatus.APPROVED
        )
        
        return {
            "date": target_date,
            "total_on_leave": len(leaves),
            "leaves": leaves
        }


leave = CRUDLeave(Leave)