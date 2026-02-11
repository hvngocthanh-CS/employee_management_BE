from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import date, time, datetime
from app.crud.base import CRUDBase
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class CRUDAttendance(CRUDBase[Attendance, AttendanceCreate, AttendanceUpdate]):
    """CRUD operations cho Attendance với advanced queries"""
    
    def get_by_employee_and_date(
        self,
        db: Session,
        employee_id: int,
        attendance_date: date
    ) -> Optional[Attendance]:
        """Get attendance record của một nhân viên trong một ngày"""
        return db.query(Attendance)\
            .filter(
                and_(
                    Attendance.employee_id == employee_id,
                    Attendance.date == attendance_date
                )
            )\
            .first()
    
    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attendance]:
        """Get attendance records của nhân viên trong khoảng thời gian"""
        query = db.query(Attendance)\
            .filter(Attendance.employee_id == employee_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        return query.order_by(Attendance.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_date(
        self,
        db: Session,
        attendance_date: date,
        department_id: Optional[int] = None,
        status: Optional[AttendanceStatus] = None
    ) -> List[Attendance]:
        """Get tất cả attendance trong một ngày"""
        query = db.query(Attendance)\
            .join(Employee, Attendance.employee_id == Employee.id)\
            .filter(Attendance.date == attendance_date)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        if status:
            query = query.filter(Attendance.status == status)
        
        return query.all()
    
    def check_in(
        self,
        db: Session,
        employee_id: int,
        check_in_time: Optional[time] = None,
        attendance_date: Optional[date] = None
    ) -> Attendance:
        """
        Check-in cho nhân viên
        Tự động xác định status dựa trên thời gian
        """
        if attendance_date is None:
            attendance_date = date.today()
        
        if check_in_time is None:
            check_in_time = datetime.now().time()
        
        # Check nếu đã có record
        existing = self.get_by_employee_and_date(db, employee_id, attendance_date)
        if existing:
            raise ValueError(f"Attendance record already exists for {attendance_date}")
        
        # Xác định status (giả sử giờ vào chuẩn là 8:00)
        standard_time = time(8, 0)
        status = AttendanceStatus.LATE if check_in_time > standard_time else AttendanceStatus.PRESENT
        
        attendance = Attendance(
            employee_id=employee_id,
            date=attendance_date,
            check_in_time=check_in_time,
            status=status
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        return attendance
    
    def check_out(
        self,
        db: Session,
        employee_id: int,
        check_out_time: Optional[time] = None,
        attendance_date: Optional[date] = None
    ) -> Attendance:
        """Check-out cho nhân viên"""
        if attendance_date is None:
            attendance_date = date.today()
        
        if check_out_time is None:
            check_out_time = datetime.now().time()
        
        attendance = self.get_by_employee_and_date(db, employee_id, attendance_date)
        if not attendance:
            raise ValueError(f"No check-in record found for {attendance_date}")
        
        if attendance.check_out_time:
            raise ValueError("Already checked out")
        
        attendance.check_out_time = check_out_time
        db.commit()
        db.refresh(attendance)
        
        return attendance
    
    def get_monthly_report(
        self,
        db: Session,
        employee_id: int,
        month: int,
        year: int
    ) -> dict:
        """
        Báo cáo chấm công theo tháng
        """
        attendances = db.query(Attendance)\
            .filter(
                and_(
                    Attendance.employee_id == employee_id,
                    extract('month', Attendance.date) == month,
                    extract('year', Attendance.date) == year
                )
            )\
            .all()
        
        # Tính toán statistics
        total_days = len(attendances)
        present = sum(1 for a in attendances if a.status == AttendanceStatus.PRESENT)
        late = sum(1 for a in attendances if a.status == AttendanceStatus.LATE)
        absent = sum(1 for a in attendances if a.status == AttendanceStatus.ABSENT)
        half_day = sum(1 for a in attendances if a.status == AttendanceStatus.HALF_DAY)
        
        # Tính tổng giờ làm việc
        total_hours = 0
        for a in attendances:
            if a.check_in_time and a.check_out_time:
                check_in = datetime.combine(date.today(), a.check_in_time)
                check_out = datetime.combine(date.today(), a.check_out_time)
                hours = (check_out - check_in).total_seconds() / 3600
                total_hours += hours
        
        return {
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "total_days": total_days,
            "present_days": present,
            "late_days": late,
            "absent_days": absent,
            "half_days": half_day,
            "working_hours": round(total_hours, 2),
            "attendances": attendances
        }
    
    def get_daily_summary(
        self,
        db: Session,
        attendance_date: date,
        department_id: Optional[int] = None
    ) -> dict:
        """Tổng hợp chấm công theo ngày"""
        query = db.query(
            func.count(Attendance.id).label('total'),
            func.count(
                func.nullif(Attendance.status == AttendanceStatus.PRESENT, False)
            ).label('present'),
            func.count(
                func.nullif(Attendance.status == AttendanceStatus.LATE, False)
            ).label('late'),
            func.count(
                func.nullif(Attendance.status == AttendanceStatus.ABSENT, False)
            ).label('absent'),
            func.count(
                func.nullif(Attendance.status == AttendanceStatus.HALF_DAY, False)
            ).label('half_day')
        )\
        .filter(Attendance.date == attendance_date)
        
        if department_id:
            query = query.join(Employee, Attendance.employee_id == Employee.id)\
                .filter(Employee.department_id == department_id)
        
        result = query.first()
        
        return {
            "date": attendance_date,
            "total_employees": result.total,
            "present": result.present or 0,
            "late": result.late or 0,
            "absent": result.absent or 0,
            "half_day": result.half_day or 0
        }


attendance = CRUDAttendance(Attendance)