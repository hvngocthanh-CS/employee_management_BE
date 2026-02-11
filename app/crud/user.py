from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations cho User với authentication"""
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_by_employee_id(self, db: Session, employee_id: int) -> Optional[User]:
        """Get user by employee_id"""
        return db.query(User).filter(User.employee_id == employee_id).first()
    
    def get_with_employee(self, db: Session, id: int) -> Optional[User]:
        """
        Get user với employee info
        Eager load để tránh N+1 query
        """
        return db.query(User)\
            .options(joinedload(User.employee))\
            .filter(User.id == id)\
            .first()
    
    def get_multi_with_employee(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get multiple users với employee info"""
        query = db.query(User).options(joinedload(User.employee))
        
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create user với hashed password
        Override base create method
        """
        # Check if employee exists
        employee = db.query(Employee).filter(Employee.id == obj_in.employee_id).first()
        if not employee:
            raise ValueError(f"Employee with id {obj_in.employee_id} not found")
        
        # Check if employee already has a user
        existing_user = self.get_by_employee_id(db, employee_id=obj_in.employee_id)
        if existing_user:
            raise ValueError(f"Employee {obj_in.employee_id} already has a user account")
        
        # Check if username exists
        existing_username = self.get_by_username(db, username=obj_in.username)
        if existing_username:
            raise ValueError(f"Username '{obj_in.username}' already exists")
        
        db_obj = User(
            employee_id=obj_in.employee_id,
            username=obj_in.username.lower(),
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """
        Update user
        Nếu có password mới thì hash
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Hash password nếu có
        if 'password' in update_data:
            hashed_password = get_password_hash(update_data['password'])
            del update_data['password']
            update_data['hashed_password'] = hashed_password
        
        # Check username uniqueness nếu update
        if 'username' in update_data and update_data['username'] != db_obj.username:
            existing = self.get_by_username(db, username=update_data['username'])
            if existing:
                raise ValueError(f"Username '{update_data['username']}' already exists")
            update_data['username'] = update_data['username'].lower()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(
        self, 
        db: Session, 
        *, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate user với username và password
        Returns User nếu credentials đúng, None nếu sai
        """
        user = self.get_by_username(db, username=username.lower())
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def change_password(
        self,
        db: Session,
        *,
        user: User,
        old_password: str,
        new_password: str
    ) -> User:
        """
        Change user password
        Verify old password trước khi update
        """
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Old password is incorrect")
        
        # Update to new password
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def reset_password(
        self,
        db: Session,
        *,
        user: User,
        new_password: str
    ) -> User:
        """
        Reset password (admin function)
        Không cần verify old password
        """
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def activate(self, db: Session, *, user: User) -> User:
        """Activate user account"""
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user
    
    def deactivate(self, db: Session, *, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user
    
    def is_active(self, user: User) -> bool:
        """Check if user is active"""
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        """Check if user is admin"""
        return user.role == UserRole.ADMIN
    
    def is_manager(self, user: User) -> bool:
        """Check if user is manager"""
        return user.role == UserRole.MANAGER
    
    def is_manager_or_admin(self, user: User) -> bool:
        """Check if user is manager or admin"""
        return user.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def get_users_by_role(
        self,
        db: Session,
        role: UserRole,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by role"""
        return db.query(User)\
            .filter(User.role == role)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def count_by_role(self, db: Session, role: UserRole) -> int:
        """Count users by role"""
        return db.query(User).filter(User.role == role).count()
    
    def get_active_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all active users"""
        return db.query(User)\
            .filter(User.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()


user = CRUDUser(User)