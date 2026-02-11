# Hướng dẫn setup file .env

## 1. File .env là gì?

File `.env` chứa **biến môi trường** (environment variables) của ứng dụng:
- Database connection strings
- API keys
- Secret keys
- Configuration settings

## 2. Tại sao cần file .env?

✅ **Bảo mật** - Không commit secrets vào Git
✅ **Linh hoạt** - Mỗi môi trường (dev, staging, prod) có config khác nhau
✅ **Dễ quản lý** - Tập trung tất cả config ở một nơi

## 3. Cách tạo file .env

### Bước 1: Copy từ template
```bash
# Copy file env.example thành .env
cp env.example .env

# Hoặc trên Windows:
copy env.example .env
```

### Bước 2: Chỉnh sửa các giá trị

Mở file `.env` và chỉnh sửa các giá trị phù hợp:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/employee_management

# JWT Settings - QUAN TRỌNG: Phải thay đổi secret key!
SECRET_KEY=your-very-secure-secret-key-here-minimum-32-characters

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Project Settings
PROJECT_NAME=Employee Management System
VERSION=1.0.0
API_V1_STR=/api/v1
```

## 4. Tạo Secret Key an toàn

**⚠️ QUAN TRỌNG:** Không bao giờ dùng secret key mặc định trong production!

### Cách 1: Sử dụng Python
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Cách 2: Sử dụng OpenSSL
```bash
openssl rand -hex 32
```

### Cách 3: Sử dụng online tool
Truy cập: https://generate-secret.vercel.app/32

## 5. Cấu trúc file .env

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL=postgresql://user:password@host:port/database

# Format: postgresql://[user[:password]@][host][:port][/database]
# Ví dụ: postgresql://postgres:mypassword@localhost:5432/employee_management

# ============================================
# JWT SETTINGS
# ============================================
SECRET_KEY=change-this-to-a-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# CORS CONFIGURATION
# ============================================
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ============================================
# APP SETTINGS
# ============================================
PROJECT_NAME=Employee Management System
VERSION=1.0.0
API_V1_STR=/api/v1
```

## 6. Cách code đọc file .env

Trong `app/core/config.py`, đã cấu hình để đọc từ `.env`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://..."
    SECRET_KEY: str = "default-secret"
    
    class Config:
        env_file = ".env"  # ✅ Đọc từ file .env
        case_sensitive = True

settings = Settings()
```

**Cách hoạt động:**
1. Pydantic tự động đọc file `.env`
2. Nếu không tìm thấy `.env`, dùng giá trị mặc định
3. Nếu có biến môi trường system (environment variables), ưu tiên hơn

## 7. Ví dụ .env cho các môi trường

### Development (.env)
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/employee_management
SECRET_KEY=dev-secret-key-not-for-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Production (.env.production)
```env
DATABASE_URL=postgresql://user:secure_password@prod-db:5432/employee_management
SECRET_KEY=super-secure-random-key-generated-with-openssl
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## 8. Security Best Practices

✅ **DO:**
- ✅ Thêm `.env` vào `.gitignore` (đã có sẵn)
- ✅ Sử dụng `.env.example` làm template
- ✅ Tạo secret key mạnh và duy nhất
- ✅ Không commit `.env` vào Git
- ✅ Sử dụng biến môi trường system trong production (Docker, Heroku, etc.)

❌ **DON'T:**
- ❌ Commit `.env` vào Git
- ❌ Share `.env` file qua email/messaging
- ❌ Sử dụng secret key mặc định trong production
- ❌ Hardcode credentials trong code

## 9. File .gitignore

File `.env` đã được thêm vào `.gitignore`:

```gitignore
# Environment variables
.env
.env.local
.env.*.local
```

## 10. Troubleshooting

### Lỗi: File .env không được đọc

**Nguyên nhân:**
- File `.env` không tồn tại
- File `.env` ở sai thư mục (phải ở root project)
- Format file `.env` sai

**Giải pháp:**
```bash
# Kiểm tra file có tồn tại không
ls -la .env  # Linux/Mac
dir .env     # Windows

# Kiểm tra format (không có dấu cách xung quanh dấu =)
DATABASE_URL=postgresql://...  # ✅ Đúng
DATABASE_URL = postgresql://...  # ❌ Sai
```

### Lỗi: Database connection failed

**Kiểm tra:**
1. Database đã chạy chưa?
2. `DATABASE_URL` đúng format chưa?
3. Username/password đúng chưa?

```bash
# Test connection
psql $DATABASE_URL
```

## 11. Quick Start

```bash
# 1. Copy template
cp env.example .env

# 2. Tạo secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Chỉnh sửa .env với secret key vừa tạo

# 4. Kiểm tra
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

## 12. Production Deployment

Trong production, thường không dùng file `.env` mà dùng:
- **Environment Variables** của server/hosting
- **Docker secrets**
- **Kubernetes secrets**
- **CI/CD variables**

Ví dụ với Docker:
```bash
docker run -e DATABASE_URL=postgresql://... -e SECRET_KEY=... myapp
```

Hoặc với environment variables:
```bash
export DATABASE_URL=postgresql://...
export SECRET_KEY=...
python -m uvicorn app.main:app
```
