from sqlalchemy import Column, Integer, String, Text, Index, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PositionLevel(str, enum.Enum):
    """Position level enum."""
    JUNIOR = "junior"
    SENIOR = "senior"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class Position(Base):
    """Position model - Chức vụ."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    level = Column(Enum(PositionLevel, name="position_level_enum"), nullable=False, index=True)
    
    description = Column(Text, nullable=True)
    
    # Relationship
    employees = relationship(
        "Employee",
        back_populates="position",
        lazy='selectin'
    )
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_position_title', 'title'),
        Index('idx_position_code', 'code'),
        Index('idx_position_level', 'level'),
    )
    
    def __repr__(self):
        return f"<Position(id={self.id}, title='{self.title}', level='{self.level}')>"
