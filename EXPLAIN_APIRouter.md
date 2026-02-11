# APIRouter trong FastAPI - Giải thích chi tiết

## 1. APIRouter là gì?

`APIRouter` là một class trong FastAPI dùng để **nhóm các routes lại với nhau**, giống như:
- **Blueprints** trong Flask
- **Routers** trong Express.js (Node.js)
- **Controllers** trong Spring Boot

## 2. Tại sao cần APIRouter?

### ❌ KHÔNG dùng APIRouter (BAD Practice)

```python
# main.py - TẤT CẢ routes trong 1 file
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/v1/departments/")
def create_department():
    ...

@app.get("/api/v1/departments/")
def get_departments():
    ...

@app.post("/api/v1/employees/")
def create_employee():
    ...

@app.get("/api/v1/employees/")
def get_employees():
    ...

@app.post("/api/v1/salaries/")
def create_salary():
    ...

# ... 100+ endpoints trong 1 file 😱
# File này sẽ dài hàng nghìn dòng, rất khó maintain!
```

**Vấn đề:**
- ❌ File quá dài, khó đọc
- ❌ Khó tìm code
- ❌ Khó làm việc nhóm (conflict khi merge)
- ❌ Khó test từng phần
- ❌ Khó maintain

### ✅ CÓ dùng APIRouter (GOOD Practice)

```python
# main.py - CHỈ import và include routers
from fastapi import FastAPI
from app.api.v1 import departments, employees

app = FastAPI()

app.include_router(departments.router, prefix="/api/v1/departments")
app.include_router(employees.router, prefix="/api/v1/employees")

# File ngắn gọn, rõ ràng! ✅
```

```python
# app/api/v1/departments.py - Mỗi file quản lý 1 domain
from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def create_department():
    ...

@router.get("/")
def get_departments():
    ...

# Chỉ có code liên quan đến departments ✅
```

**Lợi ích:**
- ✅ Code organized, dễ đọc
- ✅ Dễ tìm code (search theo file)
- ✅ Nhiều người làm việc song song
- ✅ Test từng module riêng
- ✅ Dễ maintain và mở rộng

## 3. Cách dùng APIRouter trong dự án này

### Hiện tại (Đã đúng rồi):

```python
# app/api/v1/departments.py
router = APIRouter()

@router.post("/", response_model=Department)
def create_department(...):
    ...

@router.get("/", response_model=List[Department])
def get_departments(...):
    ...

# app/main.py
app.include_router(
    departments.router,
    prefix=f"{settings.API_V1_STR}/departments",
    tags=["Departments"]
)
```

### Có thể cải thiện thêm:

```python
# app/api/v1/departments.py - VERSION CẢI THIỆN
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user

# Tạo router với config chung
router = APIRouter(
    prefix="/api/v1/departments",  # Prefix ở đây thay vì main.py
    tags=["Departments"],
    dependencies=[Depends(get_current_user)],  # Tất cả endpoints cần auth
    responses={404: {"description": "Not found"}}  # Response mặc định
)

@router.post("/", response_model=Department)
def create_department(...):
    ...

# main.py - Ngắn gọn hơn
app.include_router(departments.router)  # Không cần prefix nữa
```

## 4. Các tính năng của APIRouter

### a) Prefix - Thêm prefix chung

```python
# Cách 1: Prefix trong APIRouter
router = APIRouter(prefix="/api/v1/departments")

@router.get("/")  # Sẽ thành /api/v1/departments/
def get_departments():
    ...

# Cách 2: Prefix khi include (hiện tại đang dùng)
router = APIRouter()

@router.get("/")  # Relative path
def get_departments():
    ...

app.include_router(router, prefix="/api/v1/departments")  # Full path
```

### b) Tags - Nhóm trong Swagger UI

```python
router = APIRouter(tags=["Departments"])

# Tất cả endpoints trong router này sẽ có tag "Departments"
# Trong Swagger UI sẽ được nhóm lại với nhau
```

### c) Dependencies - Shared dependencies

```python
# Tất cả endpoints cần authentication
router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def get_departments():
    # Tự động có current_user available
    ...

@router.post("/")
def create_department():
    # Cũng tự động có current_user
    ...
```

### d) Responses - Default responses

```python
router = APIRouter(
    responses={
        404: {"description": "Not found"},
        403: {"description": "Forbidden"}
    }
)
```

### e) Response Class - Custom response class

```python
from fastapi.responses import JSONResponse

router = APIRouter(default_response_class=JSONResponse)
```

## 5. Advanced: Nested Routers

```python
# app/api/v1/departments.py
router = APIRouter()

# Sub-router cho department employees
employees_router = APIRouter(prefix="/{department_id}/employees")

@employees_router.get("/")
def get_department_employees(department_id: int):
    ...

# Include sub-router vào main router
router.include_router(employees_router)

# Kết quả: /api/v1/departments/{department_id}/employees/
```

## 6. So sánh với các framework khác

### Flask (Python)
```python
# Flask Blueprint (tương tự APIRouter)
from flask import Blueprint

bp = Blueprint('departments', __name__, url_prefix='/api/v1/departments')

@bp.route('/')
def get_departments():
    ...

app.register_blueprint(bp)
```

### Express.js (Node.js)
```javascript
// Express Router
const router = express.Router();

router.get('/', (req, res) => {
    ...
});

app.use('/api/v1/departments', router);
```

### Django (Python)
```python
# Django URL routing (tương tự)
from django.urls import path, include

urlpatterns = [
    path('api/v1/departments/', include('departments.urls')),
]
```

## 7. Best Practices

✅ **DO:**
- Tách routes theo domain/module
- Sử dụng prefix và tags
- Shared dependencies cho router
- Group related endpoints

❌ **DON'T:**
- Tất cả routes trong 1 file
- Không dùng APIRouter
- Duplicate prefix ở nhiều nơi
- Mix nhiều domains trong 1 router

## 8. Tóm tắt

**APIRouter giúp:**
1. ✅ **Organize code** - Code sạch, có tổ chức
2. ✅ **Scalability** - Dễ mở rộng
3. ✅ **Maintainability** - Dễ maintain
4. ✅ **Teamwork** - Nhiều người làm việc song song
5. ✅ **Testing** - Test từng module riêng
6. ✅ **Reusability** - Tái sử dụng router

**Trong dự án này:**
- ✅ Đã sử dụng APIRouter đúng cách
- ✅ Tách routes theo module (departments, employees, etc.)
- ✅ Include router trong main.py với prefix và tags

**Có thể cải thiện:**
- Thêm dependencies chung vào router
- Thêm responses mặc định
- Sử dụng prefix trong router thay vì khi include
