# Employee Management System

A comprehensive employee management system built with FastAPI, PostgreSQL, and SQLAlchemy.

## Features

- **Departments Management**: Create and manage departments
- **Positions Management**: Manage job positions with levels (junior, senior, manager, director, executive)
- **Employee Management**: Complete employee information with department and position assignments
- **User Authentication**: JWT-based authentication with role-based access control (admin, manager, employee)
- **Salary Management**: Track employee salaries with effective dates
- **Attendance Tracking**: Record and manage employee attendance
- **Leave Management**: Handle leave requests with approval workflow

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **JWT**: JSON Web Tokens for authentication
- **Pydantic**: Data validation using Python type annotations

## Project Structure

```
employee-management/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   │
│   ├── models/                 # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── department.py
│   │   ├── position.py
│   │   ├── employee.py
│   │   ├── user.py
│   │   ├── salary.py
│   │   ├── attendance.py
│   │   └── leave.py
│   │
│   ├── schemas/                # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── department.py
│   │   ├── position.py
│   │   ├── employee.py
│   │   ├── user.py
│   │   ├── salary.py
│   │   ├── attendance.py
│   │   └── leave.py
│   │
│   ├── crud/                   # CRUD Operations
│   │   ├── __init__.py
│   │   ├── department.py
│   │   ├── position.py
│   │   ├── employee.py
│   │   ├── user.py
│   │   ├── salary.py
│   │   ├── attendance.py
│   │   └── leave.py
│   │
│   ├── api/                    # API Endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # Login, register
│   │       ├── departments.py
│   │       ├── positions.py
│   │       ├── employees.py
│   │       ├── salaries.py
│   │       ├── attendances.py
│   │       └── leaves.py
│   │
│   ├── core/                   # Core configs
│   │   ├── __init__.py
│   │   ├── config.py           # Settings
│   │   ├── security.py         # Password hash, JWT
│   │   └── deps.py             # Dependencies (get_current_user)
│   │
│   └── utils/                  # Helper functions
│       ├── __init__.py
│       └── helpers.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── .env                        # Environment variables
├── .gitignore                  # Git ignore
├── requirements.txt            # Dependencies
├── alembic.ini                 # Alembic config
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Docker image
└── README.md                   # Documentation
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd employee_management
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file**
   ```bash
   cp .env.example .env
   ```
   
   Update the `.env` file with your database credentials:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/employee_management
   SECRET_KEY=your-secret-key-here
   ```

5. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb employee_management
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Using Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `GET /api/v1/auth/me` - Get current user information

### Departments
- `GET /api/v1/departments` - Get all departments
- `GET /api/v1/departments/{id}` - Get a department by ID
- `POST /api/v1/departments` - Create a new department (Manager/Admin)
- `PUT /api/v1/departments/{id}` - Update a department (Manager/Admin)
- `DELETE /api/v1/departments/{id}` - Delete a department (Admin)

### Positions
- `GET /api/v1/positions` - Get all positions
- `GET /api/v1/positions/{id}` - Get a position by ID
- `POST /api/v1/positions` - Create a new position (Manager/Admin)
- `PUT /api/v1/positions/{id}` - Update a position (Manager/Admin)
- `DELETE /api/v1/positions/{id}` - Delete a position (Admin)

### Employees
- `GET /api/v1/employees` - Get all employees
- `GET /api/v1/employees/{id}` - Get an employee by ID
- `POST /api/v1/employees` - Create a new employee (Manager/Admin)
- `PUT /api/v1/employees/{id}` - Update an employee (Manager/Admin)
- `DELETE /api/v1/employees/{id}` - Delete an employee (Admin)

### Salaries
- `GET /api/v1/salaries` - Get all salaries
- `GET /api/v1/salaries/{id}` - Get a salary by ID
- `GET /api/v1/salaries/employee/{employee_id}/current` - Get current salary
- `POST /api/v1/salaries` - Create a new salary (Manager/Admin)
- `PUT /api/v1/salaries/{id}` - Update a salary (Manager/Admin)
- `DELETE /api/v1/salaries/{id}` - Delete a salary (Manager/Admin)

### Attendances
- `GET /api/v1/attendances` - Get all attendances
- `GET /api/v1/attendances/{id}` - Get an attendance by ID
- `GET /api/v1/attendances/employee/{employee_id}/month/{year}/{month}` - Get monthly attendance
- `POST /api/v1/attendances` - Create a new attendance (Manager/Admin)
- `PUT /api/v1/attendances/{id}` - Update an attendance (Manager/Admin)
- `DELETE /api/v1/attendances/{id}` - Delete an attendance (Manager/Admin)

### Leaves
- `GET /api/v1/leaves` - Get all leaves
- `GET /api/v1/leaves/{id}` - Get a leave by ID
- `GET /api/v1/leaves/pending` - Get pending leaves (Manager/Admin)
- `POST /api/v1/leaves` - Create a new leave request
- `PUT /api/v1/leaves/{id}` - Update a leave request
- `POST /api/v1/leaves/{id}/approve` - Approve/reject a leave (Manager/Admin)
- `DELETE /api/v1/leaves/{id}` - Delete a leave request

## Database Features

### Indexes
The database includes optimized indexes for:
- Primary keys (automatic)
- Foreign keys for faster joins
- Frequently queried fields (name, email, employee_code, etc.)
- Composite indexes for common query patterns
- Date ranges for filtering and sorting

### Constraints
- Unique constraints on employee_code, email, username
- Check constraints on salary (must be positive)
- Date range validations
- Foreign key constraints with appropriate CASCADE/SET NULL actions

### SQL Optimization Techniques Used
1. **Indexes**: Single column and composite indexes on frequently queried fields
2. **Eager Loading**: Using `joinedload` to prevent N+1 query problems
3. **Query Optimization**: Efficient filtering, pagination, and sorting
4. **Connection Pooling**: Configured in SQLAlchemy for better performance
5. **Transaction Management**: Proper use of database transactions

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Roles and Permissions

- **Admin**: Full access to all endpoints
- **Manager**: Can create, update, and delete most resources (except users)
- **Employee**: Can view most resources and manage their own leave requests

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

## License

This project is licensed under the MIT License.
