from sqlalchemy import Column, Numeric, Integer, Float, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Salary(Base):
    """Salary model"""
    __tablename__ = "salaries"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    base_salary = Column(Numeric(15, 2), nullable=False)
    
    # Effective Period
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    employee = relationship("Employee", back_populates="salaries")
    
    # Constraints
    __table_args__ = (
         # Check constraint
        CheckConstraint('base_salary > 0', name='check_salary_positive'),
        CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='check_salary_dates'),
        
        # Indexes for better query performance
        Index('idx_salary_employee', 'employee_id'),
        Index('idx_salary_effective_from', 'effective_from'),
        Index('idx_salary_effective_to', 'effective_to'),
        
        # Composite index for active salary queries
        Index('idx_salary_employee_date', 'employee_id', 'effective_from', 'effective_to'),
    )
    
    def __repr__(self):
        return f"<Salary(id={self.id}, employee_id={self.employee_id}, salary={self.base_salary})>"
