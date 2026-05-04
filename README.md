# goit-pythonweb-hw-10 — Contacts REST API (FastAPI + PostgreSQL + JWT)

API: contacts CRUD + search + birthdays (next 7 days), JWT auth, email verification (Mailtrap), only-own contacts, rate limit (/api/users/me 5/min), avatar upload (Cloudinary), CORS.  
Swagger: http://127.0.0.1:8000/docs

## Run

docker compose up --build -d

## .env

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

## Migrations

docker compose exec api python -m alembic upgrade head

## Endpoints

POST /api/auth/signup (201/409)
POST /api/auth/login (username=email, password)
GET /api/auth/verify?token=...

GET /api/users/me (5/min)
PATCH /api/users/avatar

POST /api/contacts (201)
GET /api/contacts
GET /api/contacts/{id}
PUT /api/contacts/{id}
DELETE /api/contacts/{id}
GET /api/contacts/birthdays?days=7

## Notes

Authorization: Bearer <access_token>
Passwords hashed (bcrypt)
Email must be verified

## Documentation (Sphinx)

Build HTML docs (inside Docker container):
docker compose exec api rm -rf docs/\_build
docker compose exec api sphinx-build -b html docs docs/\_build/html

Docs output (inside container):
docs/\_build/html/index.html
