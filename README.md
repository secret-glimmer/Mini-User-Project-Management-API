# Mini User & Project Management API

Async FastAPI REST API for managing users and projects with a one-to-many relationship.
Built with **FastAPI**, **SQLModel**, **AsyncPG**, and **PostgreSQL**.

## Run

```bash
docker-compose up
```

No extra steps required. The database schema is created automatically on startup.

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Users

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Create a user (unique email, returns 409 on duplicate) |
| `GET` | `/users` | List users with pagination (`limit`, `offset`) |
| `GET` | `/users/{user_id}` | Get a user by UUID |
| `DELETE` | `/users/{user_id}` | Delete a user (cascade-deletes projects) |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/projects` | Create a project for an existing user |
| `GET` | `/projects/{project_id}` | Get a project by UUID |
| `GET` | `/users/{user_id}/projects` | List all projects for a user |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (verifies DB connectivity) |

## Configuration

All settings are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://…` | Async database connection string |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Max overflow connections |
| `DB_POOL_RECYCLE` | `3600` | Recycle connections after N seconds |
| `LOG_LEVEL` | `INFO` | Logging level |

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```
