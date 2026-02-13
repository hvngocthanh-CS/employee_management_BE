"""
FastAPI Main Application
=========================

This is the entry point for the Employee Management System API.

What happens when this starts:
1. Creates FastAPI app with configuration
2. Creates database tables (if they don't exist)
3. Sets up CORS middleware
4. Registers API routers
5. Listens for HTTP requests on http://localhost:8000

Key endpoints:
- GET /  -> API info
- GET /health -> Health check
- GET /docs -> Interactive Swagger UI (automatic documentation)
- /api/v1/departments -> Department CRUD endpoints
- /api/v1/employees -> Employee CRUD endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.database import engine, Base

# ========================
# 1. CREATE FASTAPI APP
# ========================
app = FastAPI(
    title=settings.PROJECT_NAME,  # "Employee Management System"
    version=settings.VERSION,     # "1.0.0"
    description="Employee Management System API for learning FastAPI + SQLAlchemy",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # /api/v1/openapi.json
    docs_url="/docs",     # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"    # ReDoc at http://localhost:8000/redoc
)


# ========================
# 2. CREATE DATABASE TABLES
# ========================
# This runs once on startup and creates tables if they don't exist
def create_tables():
    """
    Create all database tables defined in models.
    
    SQLAlchemy reads all model classes that inherit from Base
    and creates their corresponding tables in the database.
    
    Models:
    - Department (app/models/department.py)
    - Employee (app/models/employee.py)
    """
    Base.metadata.create_all(bind=engine)

# Call create_tables immediately when app starts
create_tables()


# ========================
# 3. SETUP CORS MIDDLEWARE
# ========================
# CORS = Cross-Origin Resource Sharing
# Allows frontend at different URL to call this API
# Without CORS, browser blocks the request for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:3000", "http://localhost:8000"]
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],     # Allow all headers
)


# ========================
# 4. REGISTER API ROUTERS
# ========================
# Include all API v1 routes (departments, employees, etc)
# This adds the route prefix /api/v1 to all included routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# ========================
# 5. ROOT ENDPOINT
# ========================
@app.get("/")
async def root():
    """
    Root endpoint - returns API information.
    
    This is the first thing users see when they navigate to the API.
    """
    return {
        "message": "Employee Management System API",
        "version": settings.VERSION,
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc",
        "health": "http://localhost:8000/health"
    }


# ========================
# 6. HEALTH CHECK ENDPOINT
# ========================
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the API. Useful for monitoring and
    checking if the server is running.
    
    Response: {"status": "healthy", "app_name": "..."}
    """
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


# ========================
# 7. RUN APPLICATION
# ========================
if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(
        "app.main:app",  # Module:app
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,       # Port number
        reload=True      # Auto-reload on code changes (development only)
    )
