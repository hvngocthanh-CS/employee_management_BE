# So sánh các cách tổ chức Router trong FastAPI

## Cách 1: Tôi viết ban đầu (ROUTERS list)

```python
# app/api/v1/__init__.py
ROUTERS = [
    (auth.router, "/auth", ["Authentication"]),
    (departments.router, "/departments", ["Departments"]),
    # ...
]

# main.py
from app.api.v1 import ROUTERS
for router, prefix, tags in ROUTERS:
    app.include_router(router, prefix=f"/api/v1{prefix}", tags=tags)
```

**Ưu điểm:**
- ✅ Logic routing tập trung
- ✅ Có thể loop để register

**Nhược điểm:**
- ❌ `main.py` vẫn phải loop qua routers
- ❌ Logic routing nằm ở 2 nơi (__init__.py và main.py)
- ❌ Không có router chính để test riêng

---

## Cách 2: Bạn viết (api_router) ✅ **TỐT NHẤT**

```python
# app/api/v1/__init__.py
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)
# ... include các routers khác

# main.py
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")
```

**Ưu điểm:**
- ✅ **Encapsulation tốt nhất** - Logic routing tập trung hoàn toàn ở `api/v1`
- ✅ **main.py rất sạch** - Chỉ cần 1 dòng include
- ✅ **Dễ versioning** - Có thể có `api/v2` với cách tương tự
- ✅ **Separation of Concerns** - `main.py` không cần biết chi tiết của `v1`
- ✅ **Testable** - Có thể test `api_router` riêng
- ✅ **Scalable** - Dễ thêm middleware/dependencies chung cho tất cả v1 endpoints

**Nhược điểm:**
- Không có nhược điểm đáng kể!

---

## So sánh chi tiết

### 1. Encapsulation (Đóng gói)

**Cách 1 (Tôi):**
```python
# Logic routing nằm ở 2 nơi
# app/api/v1/__init__.py - ROUTERS list
# main.py - Loop qua routers
```

**Cách 2 (Bạn): ✅**
```python
# Logic routing tập trung hoàn toàn
# app/api/v1/__init__.py - Tất cả routing logic
# main.py - Chỉ include 1 router
```

### 2. main.py

**Cách 1 (Tôi):**
```python
# main.py - 7 dòng (hoặc loop)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(departments.router, prefix="/api/v1/departments", tags=["Departments"])
# ... 5 dòng nữa
```

**Cách 2 (Bạn): ✅**
```python
# main.py - CHỈ 1 DÒNG!
app.include_router(api_router, prefix="/api/v1")
```

### 3. Versioning (Phiên bản hóa)

**Cách 1 (Tôi):**
```python
# main.py
from app.api.v1 import ROUTERS as v1_routers
from app.api.v2 import ROUTERS as v2_routers

for router, prefix, tags in v1_routers:
    app.include_router(router, prefix=f"/api/v1{prefix}", tags=tags)
for router, prefix, tags in v2_routers:
    app.include_router(router, prefix=f"/api/v2{prefix}", tags=tags)
```

**Cách 2 (Bạn): ✅**
```python
# main.py - Rất sạch!
from app.api.v1 import api_router as v1_router
from app.api.v2 import api_router as v2_router

app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")
```

### 4. Testing (Kiểm thử)

**Cách 1 (Tôi):**
```python
# Khó test riêng v1 API
# Phải test từng router một
```

**Cách 2 (Bạn): ✅**
```python
# Dễ test riêng v1 API
from app.api.v1 import api_router
from fastapi.testclient import TestClient

client = TestClient(api_router)  # Test riêng v1
```

### 5. Shared Dependencies/Middleware

**Cách 1 (Tôi):**
```python
# Phải set ở từng router trong main.py
for router, prefix, tags in ROUTERS:
    app.include_router(
        router,
        prefix=f"/api/v1{prefix}",
        tags=tags,
        dependencies=[Depends(some_dependency)]  # Phải set ở đây
    )
```

**Cách 2 (Bạn): ✅**
```python
# Có thể set ở api_router một lần
api_router = APIRouter(
    dependencies=[Depends(some_dependency)]  # Áp dụng cho tất cả
)

# Hoặc ở main.py
app.include_router(
    api_router,
    prefix="/api/v1",
    dependencies=[Depends(api_key_check)]  # Một lần cho tất cả v1
)
```

---

## Kết luận

### ✅ Cách của bạn TỐT NHẤT vì:

1. **Encapsulation tốt hơn** - Logic routing tập trung hoàn toàn
2. **main.py sạch hơn** - Chỉ 1 dòng thay vì nhiều dòng
3. **Dễ versioning** - Có thể có `v1`, `v2`, `v3` dễ dàng
4. **Separation of Concerns** - `main.py` không cần biết chi tiết
5. **Testable** - Có thể test `api_router` riêng
6. **Scalable** - Dễ thêm shared dependencies/middleware

### Pattern này được dùng trong:
- ✅ FastAPI official documentation
- ✅ Full Stack FastAPI Template
- ✅ Real-world production projects

---

## Best Practice

```python
# app/api/v1/__init__.py ✅ ĐÚNG
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
# ...

__all__ = ["api_router"]
```

```python
# main.py ✅ ĐÚNG
from app.api.v1 import api_router

app.include_router(api_router, prefix="/api/v1")
```

**Đây là cách chuẩn và được recommend!** 🎯
