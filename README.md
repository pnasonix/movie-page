# gporn.me - Flask App (Dockerized)

## Requirements
- Docker 24+

## Build
```bash
docker build -t gporn-me:latest .
```

## Run
SQLite DB will be created inside the container unless you mount a volume.
```bash
docker run --rm -p 5001:5001 --name gporn-me gporn-me:latest
```
Open http://localhost:5001

To persist the SQLite database and logs:
```bash
docker run --rm -p 5001:5001 \
  -v $(pwd)/instance:/app/instance \
  --name gporn-me gporn-me:latest
```

## Environment
The app auto-creates tables on start. You can override defaults:
- `SECRET_KEY` (optional)
- `DATABASE_URL` (defaults to `sqlite:///movies.db`)

## Notes
- Gunicorn serves the app by default.
- `.dockerignore` excludes dev files and local instance data from the image.

