# SQL Features và Optimization Techniques

Dự án này sử dụng các kỹ thuật SQL và SQLAlchemy để tối ưu hóa hiệu suất và đảm bảo tính toàn vẹn dữ liệu.

## 1. Indexes (Chỉ mục)

### Single Column Indexes
```python
# Tự động tạo index cho primary key
id = Column(Integer, primary_key=True, index=True)

# Index trên các cột thường xuyên query
name = Column(String(100), nullable=False, index=True)
email = Column(String(100), unique=True, nullable=False, index=True)
employee_code = Column(String(50), unique=True, nullable=False, index=True)
```

### Composite Indexes (Chỉ mục kết hợp)
```python
# Index kết hợp cho query thường xuyên sử dụng
__table_args__ = (
    Index('idx_employee_dept_status', 'department_id', 'employment_status'),
    Index('idx_attendance_employee_date', 'employee_id', 'date'),
    Index('idx_salary_employee_date', 'employee_id', 'effective_from', 'effective_to'),
)
```

### Unique Constraints với Index
```python
# Unique constraint tự động tạo unique index
email = Column(String(100), unique=True, nullable=False)
employee_code = Column(String(50), unique=True, nullable=False)
```

## 2. Foreign Keys và Relationships

### Foreign Key Constraints
```python
# Foreign key với CASCADE delete
employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))

# Foreign key với SET NULL
department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))
```

### Relationships với Lazy Loading
```python
# One-to-Many relationship
employee = relationship("Employee", back_populates="attendances")

# Many-to-One relationship
department = relationship("Department", back_populates="employees")
```

### Eager Loading để tránh N+1 Problem
```python
# Sử dụng joinedload để load relationships trong một query
def get(db: Session, employee_id: int):
    return db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.position)
    ).filter(Employee.id == employee_id).first()
```

## 3. Constraints (Ràng buộc)

### Check Constraints
```python
__table_args__ = (
    CheckConstraint('base_salary > 0', name='check_salary_positive'),
    CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', 
                   name='check_date_range'),
)
```

### Unique Constraints
```python
# Unique constraint trên nhiều cột
__table_args__ = (
    UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
)
```

## 4. Query Optimization

### Efficient Filtering
```python
# Sử dụng filter với điều kiện rõ ràng
query = db.query(Employee).filter(
    and_(
        Employee.department_id == department_id,
        Employee.employment_status == EmploymentStatus.ACTIVE
    )
)
```

### Pagination
```python
# Offset và limit cho pagination
def get_multi(db: Session, skip: int = 0, limit: int = 100):
    return query.offset(skip).limit(limit).all()
```

### Sorting
```python
# Sắp xếp kết quả
return query.order_by(desc(Employee.created_at)).all()
```

### Aggregations
```python
# Sử dụng func để aggregation
stats = db.query(
    Attendance.status,
    func.count(Attendance.id).label('count')
).filter(...).group_by(Attendance.status).all()
```

### Date Queries
```python
# Query theo năm/tháng
query = db.query(Leave).filter(
    and_(
        func.extract('year', Leave.start_date) == year,
        func.extract('month', Leave.start_date) == month
    )
)
```

### Range Queries
```python
# Query trong khoảng thời gian
query = db.query(Salary).filter(
    and_(
        Salary.effective_from <= effective_date,
        or_(
            Salary.effective_to.is_(None),
            Salary.effective_to >= effective_date
        )
    )
)
```

## 5. Connection Pooling

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Kiểm tra connection trước khi dùng
    pool_size=10,        # Số connection trong pool
    max_overflow=20,     # Số connection tối đa khi cần
)
```

## 6. Transactions

```python
# Sử dụng transaction để đảm bảo tính toàn vẹn dữ liệu
def create(db: Session, *, obj_in: DepartmentCreate):
    db_obj = Department(**obj_in.dict())
    db.add(db_obj)
    db.commit()      # Commit transaction
    db.refresh(db_obj)  # Refresh để lấy giá trị từ DB
    return db_obj
```

## 7. Raw SQL Queries (Khi cần)

SQLAlchemy cũng hỗ trợ raw SQL queries:

```python
# Ví dụ raw SQL
result = db.execute(
    text("SELECT * FROM employees WHERE department_id = :dept_id"),
    {"dept_id": department_id}
).fetchall()
```

## 8. Database Migrations với Alembic

### Tự động generate migration từ models
```bash
alembic revision --autogenerate -m "Description"
```

### Apply migrations
```bash
alembic upgrade head
```

## 9. Query Patterns Thường Dùng

### Full-text Search
```python
query = db.query(Employee).filter(
    or_(
        Employee.full_name.ilike(f"%{search}%"),
        Employee.email.ilike(f"%{search}%")
    )
)
```

### Conditional Joins
```python
# Left join với điều kiện
query = db.query(Employee).outerjoin(Department).filter(...)
```

### Subqueries
```python
# Sử dụng subquery
subquery = db.query(Salary.employee_id).filter(...).subquery()
query = db.query(Employee).filter(Employee.id.in_(select([subquery.c.employee_id])))
```

## 10. Performance Best Practices

1. **Index Frequently Queried Columns**: Tạo index cho các cột thường xuyên query
2. **Use Composite Indexes**: Tạo composite index cho các query phức tạp
3. **Avoid N+1 Queries**: Sử dụng eager loading (joinedload, selectinload)
4. **Limit Results**: Luôn sử dụng pagination cho list queries
5. **Use Appropriate Data Types**: Chọn data type phù hợp để tiết kiệm storage
6. **Monitor Query Performance**: Sử dụng SQLAlchemy echo=True để debug slow queries

## 11. Database Design Principles

- **Normalization**: Database được normalize để tránh data redundancy
- **Foreign Keys**: Sử dụng foreign keys để đảm bảo referential integrity
- **Constraints**: Sử dụng constraints để đảm bảo data integrity
- **Indexes**: Tạo indexes trên các cột thường xuyên query để tăng tốc độ
- **Partitioning**: Có thể partition các bảng lớn theo thời gian (future enhancement)
