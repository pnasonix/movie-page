# Hướng dẫn Deploy lên Server khác với Docker

## Files cần copy để chạy Docker

### 1. Files bắt buộc (core application)
```
app.py
requirements.txt
Dockerfile
.dockerignore
```

### 2. Templates (HTML)
```
templates/
  ├── admin/
  │   ├── add_movie.html
  │   ├── base.html
  │   ├── categories.html
  │   ├── dashboard.html
  │   ├── edit_movie.html
  │   ├── movies.html
  │   └── users.html
  ├── errors/
  │   ├── 404.html
  │   └── 500.html
  ├── base.html
  ├── category.html
  ├── favorites.html
  ├── index.html
  ├── login.html
  ├── movie.html
  ├── profile.html
  ├── register.html
  └── search.html
```

### 3. Static files (CSS, JS)
```
static/
  ├── css/
  │   ├── admin.css
  │   └── style.css
  └── js/
      └── main.js
```

### 4. Uploads (nếu có dữ liệu cần giữ lại)
```
static/uploads/
  ├── avatars/     # (nếu có avatar users)
  ├── movies/      # (nếu có video files)
  └── posters/     # (nếu có poster images)
```

### 5. Optional utilities (không bắt buộc cho Docker)
```
add_movie.py       # Script utility (optional)
create_admin.py    # Script utility (optional)
README.md          # Documentation (optional)
```

## Files KHÔNG cần copy

❌ `venv/` - Virtual environment (Docker sẽ tự build)
❌ `instance/` - Database và logs (sẽ tạo mới hoặc mount volume)
❌ `__pycache__/` - Python cache
❌ `*.pyc`, `*.pyo` - Compiled Python files
❌ `.git/` - Git repository (nếu không cần)
❌ `setup_*.sh`, `restart*.sh` - Deployment scripts
❌ `nginx_*.conf`, `*.service` - Server configs (không dùng trong Docker)

## Cách copy và deploy

### Option 1: Copy toàn bộ (trừ venv và instance)
```bash
# Trên server cũ
cd /var/www/gporn.me
tar -czf gporn-deploy.tar.gz \
  --exclude='venv' \
  --exclude='instance' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  app.py requirements.txt Dockerfile .dockerignore \
  templates/ static/ add_movie.py create_admin.py README.md

# Copy file tar.gz lên server mới
scp gporn-deploy.tar.gz user@new-server:/path/to/destination/

# Trên server mới
cd /path/to/destination
tar -xzf gporn-deploy.tar.gz
```

### Option 2: Sử dụng rsync (khuyến nghị)
```bash
# Trên server cũ
cd /var/www/gporn.me

rsync -avz --exclude='venv' \
          --exclude='instance' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='*.pyc' \
          --exclude='*.pyo' \
          ./ user@new-server:/var/www/gporn.me/
```

### Option 3: Git clone (nếu đã push lên GitHub)
```bash
# Trên server mới
git clone https://github.com/USERNAME/REPO_NAME.git /var/www/gporn.me
cd /var/www/gporn.me
```

## Build và chạy Docker trên server mới

```bash
cd /var/www/gporn.me

# Build image
docker build -t gporn-me:latest .

# Chạy container (với volume cho database)
docker run -d \
  --name gporn-me \
  -p 5001:5001 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  --restart unless-stopped \
  gporn-me:latest

# Hoặc dùng docker-compose (nếu có)
docker-compose up -d
```

## Tạo admin user trên server mới

```bash
# Copy file create_admin.py nếu chưa có
docker exec -it gporn-me python create_admin.py
# Hoặc chạy trực tiếp trong container
docker exec -it gporn-me python -c "
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    admin = User(username='admin', email='admin@example.com', 
                 password_hash=generate_password_hash('your-password'),
                 is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print('Admin created!')
"
```

## Backup database trước khi copy (nếu cần)

```bash
# Trên server cũ
cp instance/movies.db instance/movies.db.backup

# Copy database lên server mới (nếu muốn giữ dữ liệu)
scp instance/movies.db user@new-server:/var/www/gporn.me/instance/
```

## Checklist trước khi deploy

- [ ] Copy `app.py`, `requirements.txt`, `Dockerfile`, `.dockerignore`
- [ ] Copy toàn bộ thư mục `templates/`
- [ ] Copy toàn bộ thư mục `static/` (bao gồm uploads nếu có)
- [ ] Tạo thư mục `instance/` trên server mới (hoặc mount volume)
- [ ] Build Docker image thành công
- [ ] Tạo admin user
- [ ] Test truy cập ứng dụng
