# gporn.me - Flask Application

Flask web application for movie streaming platform with admin panel, user authentication, and video management.

## Requirements

### For Python (Development/Production)
- Python 3.12+
- pip

### For Docker (Production)
- Docker 24+

## Installation

### Option 1: Run with Python (Development/Production)

#### 1. Clone repository
```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd gporn-me
```

#### 2. Create virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set environment variables (optional)
```bash
export SECRET_KEY="your-secret-key-change-this"
export DATABASE_URL="sqlite:///movies.db"
```

#### 5. Initialize database and create admin user
```bash
# Database will be auto-created on first run
# Create admin user
python create_admin.py
```

#### 6. Run application

**Development mode (with auto-reload):**
```bash
bash run_dev.sh
# Or directly: python app.py
```

**Production mode (with Gunicorn):**
```bash
bash run_prod.sh
# Or directly: gunicorn --workers 4 --bind 0.0.0.0:5001 --timeout 120 app:app
```

The app will be available at `http://localhost:5001`

### Option 2: Run with Docker (Production)

#### 1. Build Docker image
```bash
docker build -t gporn-me:latest .
```

#### 2. Run container

**Basic run (database in container):**
```bash
docker run --rm -p 5001:5001 --name gporn-me gporn-me:latest
```

**With persistent database and uploads:**
```bash
docker run -d \
  --name gporn-me \
  -p 5001:5001 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  --restart unless-stopped \
  gporn-me:latest
```

#### 3. Create admin user (inside container)
```bash
docker exec -it gporn-me python create_admin.py
```

The app will be available at `http://localhost:5001`

## Environment Variables

- `SECRET_KEY` (optional) - Flask secret key for sessions
- `DATABASE_URL` (optional) - Database connection string (default: `sqlite:///movies.db`)
- `CSS_VERSION` (optional) - CSS version for cache busting

## Project Structure

```
gporn-me/
├── app.py                 # Main Flask application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker build configuration
├── .dockerignore           # Files excluded from Docker image
├── run_dev.sh              # Development mode script
├── run_prod.sh             # Production mode script (Gunicorn)
├── templates/              # HTML templates
│   ├── admin/              # Admin panel templates
│   ├── errors/             # Error pages (404, 500)
│   └── ...
├── static/                 # Static files
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   └── uploads/            # User uploads (avatars, posters, movies)
├── instance/               # Instance-specific files (database, logs)
├── add_movie.py            # Utility: Add movie via CLI
└── create_admin.py         # Utility: Create admin user
```

## Features

- User authentication (login, register, profile)
- Movie streaming with resume functionality
- Admin panel for movie/category management
- Watch history and favorites
- Comments system
- Responsive design

## Development

The app runs in development mode by default when using `python app.py`:
- Auto-reload on file changes
- Debug mode enabled
- Detailed error pages

For production, use Gunicorn or Docker.

## Notes

- Database (SQLite) is auto-created in `instance/movies.db` on first run
- Uploads are stored in `static/uploads/`
- Logs are written to `instance/app.log`
- Docker image uses Gunicorn with 4 workers by default
- `.dockerignore` excludes dev files and local instance data from the image

## Deployment

See `DEPLOY.md` for detailed deployment instructions.
