# Quick Start Guide

## Chạy với Python (Nhanh nhất)

```bash
# 1. Clone repo
git clone <your-repo-url>
cd gporn-me

# 2. Tạo venv và cài đặt
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Tạo admin
python create_admin.py

# 4. Chạy (Development)
bash run_dev.sh
# Hoặc: python app.py

# 5. Chạy (Production)
bash run_prod.sh
# Hoặc: gunicorn --workers 4 --bind 0.0.0.0:5001 app:app
```

## Chạy với Docker (Khuyến nghị cho Production)

```bash
# 1. Build
docker build -t gporn-me:latest .

# 2. Run
docker run -d -p 5001:5001 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  --name gporn-me gporn-me:latest

# 3. Tạo admin
docker exec -it gporn-me python create_admin.py
```

Truy cập: http://localhost:5001
