"""
Base CRUD Class
===============
Generic CRUD (Create, Read, Update, Delete) operations.

This uses Python generics to work with any SQLAlchemy model.
All specific CRUD classes inherit from this base.
"""

from typing import Generic, TypeVar, Type, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Type variables for the generic CRUD class
ModelType = TypeVar("ModelType")  # The SQLAlchemy model (e.g., Employee)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # Create request schema
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # Update request schema


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with generic operations.
    
    This class provides standard database operations:
    - get(id): fetch single record
    - get_multi(): fetch multiple records
    - create(): insert new record
    - update(): modify existing record
    - delete(): remove record
    """
    
    def __init__(self, model: Type[ModelType]):
        """Initialize with a SQLAlchemy model class"""
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        SQL equivalent: SELECT * FROM table WHERE id = ?
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            The model instance, or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with skip/limit (pagination).
        
        SQL equivalent: SELECT * FROM table LIMIT ? OFFSET ?
        
        Args:
            db: Database session
            skip: Number of records to skip (pagination offset)
            limit: Maximum records to return
            
        Returns:
            List of model instances
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Steps:
        1. Convert Pydantic schema to dict
        2. Create model instance from dict
        3. Add to session (pending)
        4. Commit to database
        5. Refresh to get any auto-generated fields (like id)
        
        Args:
            db: Database session
            obj_in: Pydantic schema with data
            
        Returns:
            The created model instance with ID populated
        """
        obj_in_data = obj_in.model_dump()  # Convert Pydantic to dict
        db_obj = self.model(**obj_in_data)  # Create model instance
        db.add(db_obj)  # Add to session
        db.commit()  # Write to database
        db.refresh(db_obj)  # Get auto-generated fields (id, timestamps, etc)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Update an existing record.
        
        Only updates fields provided in obj_in (exclude_unset=True).
        This allows partial updates.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Pydantic schema with updated fields
            
        Returns:
            The updated model instance
        """
        obj_data = obj_in.model_dump(exclude_unset=True)  # Only provided fields
        
        # Update each field
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            The deleted model instance, or None if not found
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
