# Employee Management System

A full-stack employee management application built with FastAPI backend and WPF frontend.

## Backend (FastAPI)

### Features
- **Authentication**: JWT-based user authentication and authorization
- **Departments**: CRUD operations for managing departments
- **Positions**: CRUD operations for job positions (Junior, Senior, Manager, Director, Executive)
- **Employees**: Full employee lifecycle management
- **Users**: User account management with role-based access (Admin, Manager, Employee)
- **Salaries**: Salary tracking and history management
- **Attendances**: Employee attendance tracking and reporting
- **Leaves**: Leave request management and approval workflow

### Database Schema
- **departments**: Company departments
- **positions**: Job positions with hierarchical levels
- **employees**: Employee information linked to departments and positions
- **users**: Authentication and authorization 
- **salaries**: Salary history with effective dates
- **attendances**: Daily attendance records
- **leaves**: Leave requests with approval workflow

### Technologies
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **JWT**: Token-based authentication
- **SQLite**: Development database

### Running the Backend

```bash
cd employee_management_BE

# Install dependencies
pip install -r requirements.txt

# Create/update database
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

# Start the server
uvicorn app.main:app --reload --port 8000
```

### API Documentation
Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

#### Departments
- `GET /api/v1/departments` - List all departments
- `POST /api/v1/departments` - Create department
- `PUT /api/v1/departments/{id}` - Update department
- `DELETE /api/v1/departments/{id}` - Delete department

#### Positions
- `GET /api/v1/positions` - List all positions
- `POST /api/v1/positions` - Create position (requires auth)
- `PUT /api/v1/positions/{id}` - Update position (requires auth)
- `DELETE /api/v1/positions/{id}` - Delete position (requires auth)

#### Employees
- `GET /api/v1/employees` - List all employees
- `POST /api/v1/employees` - Create employee
- `PUT /api/v1/employees/{id}` - Update employee
- `DELETE /api/v1/employees/{id}` - Delete employee

## Frontend (WPF)

### Features
- **Dashboard**: Overview with statistics and recent activities
- **Navigation**: Modern sidebar navigation with role-based menus
- **Authentication**: Login/Register with session management
- **Department Management**: Full CRUD operations
- **Employee Management**: Employee data management
- **Position Management**: Job position management
- **Responsive Design**: Modern UI with Material Design colors

### Technologies
- **WPF (.NET 9)**: Desktop application framework
- **C#**: Programming language
- **Newtonsoft.Json**: JSON serialization
- **HttpClient**: REST API communication

### Running the Frontend

```bash
cd employee_management_FE/EmployeeManagement

# Restore packages
dotnet restore

# Build and run
dotnet run
```

### Application Flow
1. **Login/Register**: User authentication
2. **Dashboard**: Main overview page with statistics
3. **Navigation**: Access different modules via sidebar
4. **CRUD Operations**: Create, Read, Update, Delete data
5. **Session Management**: Secure token-based sessions

## Learning Objectives

This project demonstrates:

### Backend Development
- **RESTful API Design**: Proper HTTP methods and status codes
- **Database Design**: Normalized schema with relationships
- **ORM Usage**: SQLAlchemy for database operations
- **Migration Management**: Alembic for schema changes
- **Authentication**: JWT token implementation
- **Validation**: Pydantic schemas for request/response validation
- **Error Handling**: Proper exception handling and error responses
- **API Documentation**: Automatic OpenAPI documentation

### Frontend Development
- **API Integration**: Consuming REST APIs
- **Modern UI Design**: Material Design inspired interface
- **Navigation Patterns**: Frame-based navigation
- **Data Binding**: WPF data binding and MVVM patterns
- **Session Management**: Token storage and management
- **Error Handling**: User-friendly error messages

### Full-Stack Integration
- **Client-Server Communication**: HTTP request/response cycle
- **Authentication Flow**: Login, token storage, API authentication
- **Data Flow**: Frontend forms -> API -> Database -> API -> Frontend display
- **Error Propagation**: Backend errors displayed in frontend

## Project Structure

```
employee_management_BE/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Authentication & config
│   ├── crud/            # Database operations
│   ├── models/          # SQLAlchemy models
│   └── schemas/         # Pydantic schemas
├── alembic/             # Database migrations
└── test_api.py          # API testing script

employee_management_FE/
└── EmployeeManagement/
    ├── *.xaml           # UI pages
    ├── *.xaml.cs        # Page code-behind
    └── appsettings.json # Configuration
```

## Next Steps for Learning

### Backend Enhancements
1. **Add unit tests** using pytest
2. **Implement caching** with Redis
3. **Add logging** for better debugging
4. **Database optimization** with indexes and query optimization
5. **API versioning** for future updates
6. **Rate limiting** for security
7. **Background tasks** with Celery

### Frontend Enhancements
1. **Add data validation** before API calls
2. **Implement MVVM pattern** properly
3. **Add loading indicators** for better UX
4. **Error handling improvements** with retry mechanisms
5. **Offline mode** with local data caching
6. **Reports generation** with charts and exports
7. **Real-time updates** with SignalR

### DevOps & Deployment
1. **Docker containers** for easy deployment
2. **CI/CD pipeline** with GitHub Actions
3. **Production database** (PostgreSQL)
4. **Environment management** (dev/staging/prod)
5. **Monitoring & logging** in production
6. **Security hardening** and vulnerability scanning

## Contributing

This is a learning project. Feel free to:
1. Add new features
2. Improve error handling
3. Enhance UI/UX
4. Add tests
5. Optimize performance
6. Add documentation

## License

This project is for educational purposes.