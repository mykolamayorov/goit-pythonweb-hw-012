# Contacts REST API (FastAPI + PostgreSQL + JWT)

REST API for managing contacts with authentication, email verification, role-based access, caching, and full test coverage.

Swagger:
http://localhost:8000/docs

## Features

- Contacts CRUD (create, read, update, delete)
- Search by first name, last name, email
- Upcoming birthdays (next N days)
- JWT authentication:
  - access_token + refresh_token
  - refresh token rotation
- Email verification (Mailtrap)
- Password reset (token-based)
- Role-based access:
  - user / admin
  - admin-only avatar default update
- Redis caching:
  - cached current user (`get_current_user`)
- Rate limiting (`/api/users/me` — 5/min)
- Avatar upload (Cloudinary)
- CORS support

## Run project (Docker)

docker compose up --build -d

Open:
http://localhost:8000/docs

## Environment variables (.env)

DB_USER=postgres  
DB_PASSWORD=mysecretpassword  
DB_HOST=db  
DB_PORT=5432  
DB_NAME=postgres

JWT_SECRET_KEY=your_secret  
JWT_ALGORITHM=HS256  
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30

SMTP_HOST=sandbox.smtp.mailtrap.io  
SMTP_PORT=587  
SMTP_USER=your_user  
SMTP_PASSWORD=your_password  
MAIL_FROM=noreply@example.com  
APP_BASE_URL=http://localhost:8000

ME_RATE_LIMIT=5/minute

CLOUDINARY_CLOUD_NAME=your_cloud  
CLOUDINARY_API_KEY=your_key  
CLOUDINARY_API_SECRET=your_secret

CORS_ORIGINS=http://localhost:3000

ADMIN_EMAIL=admin@example.com  
DEFAULT_AVATAR_URL=https://example.com/default.png

REDIS_URL=redis://redis:6379/0

## Database migrations

docker compose exec api python -m alembic upgrade head

## API Endpoints

Auth:
POST /api/auth/signup  
POST /api/auth/login  
POST /api/auth/refresh  
GET /api/auth/verify  
POST /api/auth/password-reset/request  
POST /api/auth/password-reset/confirm

Users:
GET /api/users/me  
PATCH /api/users/avatar  
PATCH /api/users/avatar/default (admin only)

Contacts:
POST /api/contacts  
GET /api/contacts  
GET /api/contacts/{id}  
PUT /api/contacts/{id}  
DELETE /api/contacts/{id}  
GET /api/contacts/birthdays?days=7

## Documentation (Sphinx)

docker compose exec api rm -rf docs/\_build  
docker compose exec api sphinx-build -b html docs docs/\_build/html

Docs output:
docs/\_build/html/index.html

## Tests

docker compose exec api pytest -q

## Test coverage

docker compose exec api pytest --cov=app --cov-report=term-missing --cov-fail-under=75

Current coverage: ~79%

## Notes

Authorization:
Bearer <access_token>

Passwords are hashed (bcrypt)  
Email verification required  
Refresh tokens stored as hash  
Token rotation implemented (with jti)  
Redis cache invalidated on updates

## Tech stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- JWT (python-jose)
- Cloudinary
- Mailtrap
- Pytest + pytest-cov
- Sphinx
- Docker Compose
