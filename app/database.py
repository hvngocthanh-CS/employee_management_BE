"""
Database Configuration
======================
SQLAlchemy setup for synchronous database operations with SQLite.

Key concepts:
  - create_engine: Creates a connection pool to the database
  - sessionmaker: Creates a factory for database sessions
  - DeclarativeBase: Base class for all SQLAlchemy models
  - get_db: Dependency injection function for FastAPI routes
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    All model classes inherit from this to get ORM functionality.
    """
    pass


# Prepare engine configuration options
engine_kwargs = {
    "pool_pre_ping": True,  # Test connections before using them
    "echo": settings.DEBUG  # Print SQL queries if DEBUG is True
}

# SQLite-specific configuration
# SQLite doesn't need a connection pool like PostgreSQL, so we disable it
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},  # Allow multi-threaded access
        "echo": settings.DEBUG
    }

# Create the database engine
# This is the core connection to the database
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Create a session factory
# This factory creates new database sessions when needed
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit changes
    autoflush=False,   # Don't auto-flush changes
    bind=engine        # Use our engine
)


def init_db():
    """
    Initialize the database by creating all tables.
    
    This function reads all model classes that inherit from Base
    and creates their corresponding tables in the database.
    
    Usage (in main.py):
      init_db()
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get a database session for dependency injection in FastAPI routes.
    
    This is a generator that yields a database session to a route,
    then closes it when the route is done.
    
    FastAPI will automatically manage the session lifecycle by calling
    this function and cleaning up the session after the request.
    
    Usage (in API route):
      @app.get("/items")
      def get_items(db: Session = Depends(get_db)):
          return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the route
    finally:
        db.close()  # Clean up the session
