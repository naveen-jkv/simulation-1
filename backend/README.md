# AI College Notification Hub - Backend API 🎓

A production-ready REST API built with **FastAPI**, **SQLAlchemy**, **PostgreSQL** (with zero-config SQLite fallback), **Pydantic v2**, and **JWT Authentication**. It features an **OpenAI-compatible AI service** that automatically summarizes announcements, classifies them into college categories, extracts due dates/deadlines, and assesses urgency priorities with 100% resilient heuristic fallback.

---

## 🚀 Tech Stack

- **Framework**: Python 3.12+ / FastAPI
- **Database ORM**: SQLAlchemy 2.0+
- **Database Engine**: PostgreSQL (Production) / SQLite (Zero-Config Development & Testing)
- **Data Validation & Settings**: Pydantic v2 & Pydantic-Settings
- **Authentication**: JWT (JSON Web Tokens via PyJWT) & Bcrypt password hashing
- **Migrations**: Alembic
- **AI Engine**: OpenAI-compatible API client (supports OpenAI, Groq, Ollama, DeepSeek, OpenRouter)
- **Server**: Uvicorn ASGI
- **Test Suite**: Pytest & HTTPX TestClient

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app instance, CORS middleware, lifespan & error handlers
│   ├── config.py            # Environment configuration via Pydantic BaseSettings
│   ├── database.py          # SQLAlchemy engine, session maker, get_db dependency
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User model (id, name, email, password_hash, role, created_at)
│   │   └── notification.py  # Notification & NotificationRead models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth schemas (Register, Login, Token, UserResponse)
│   │   └── notification.py  # Notification schemas & AI analysis output schema
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth endpoints (register, login, me)
│   │   ├── notifications.py # /api/notifications endpoints (CRUD, search, filter, read)
│   │   └── admin.py         # /api/admin endpoints (stats, metrics, user directory)
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_service.py    # OpenAI-compatible analyzer + resilient heuristic fallback
│   └── utils/
│       ├── __init__.py
│       └── auth.py          # Bcrypt hashing, JWT creation/decoding, auth dependencies
├── alembic/                 # Database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── tests/                   # Automated pytest suite
│   ├── conftest.py          # Isolated DB session & test client fixtures
│   ├── test_auth.py         # Registration, login, and auth token tests
│   ├── test_notifications.py# CRUD, RBAC, filters & per-student read tests
│   └── test_ai_service.py   # AI structured output & fallback resilience tests
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚡ Quickstart & Setup

### 1. Prerequisites
- Python 3.12+
- (Optional) PostgreSQL server running locally or in Docker

### 2. Install Dependencies
In the `backend` directory:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Database: Use PostgreSQL or leave default for instant SQLite zero-setup
DATABASE_URL=sqlite:///./college_hub.db
# For PostgreSQL:
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/college_hub

# JWT Secret
SECRET_KEY=college_notification_hub_hackathon_super_secret_key_2026_jwt_token
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Configuration (Optional: Works without key using deterministic fallback)
OPENAI_API_KEY=your_openai_or_groq_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# CORS: Set allowed origins for frontend teammate (or * for all)
CORS_ORIGINS=*
```

### 4. Database Migrations
Run Alembic migrations to initialize the database:
```bash
alembic upgrade head
```
*(Note: The application also auto-creates all tables on startup via SQLAlchemy metadata, ensuring zero friction.)*

### 5. Start the Server
Run with Uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Interactive Documentation
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Automated Tests

Run the full automated test suite:
```bash
python -m pytest tests -v
```

---

## 🤖 AI Categorization & Fallback Resilience

When an admin posts an announcement:
1. The backend sends the text to the configured OpenAI-compatible LLM endpoint.
2. The model extracts:
   - **`summary`**: Concise 1-2 sentence executive summary.
   - **`category`**: Strictly mapped to: `Academic`, `Exam`, `Assignment`, `Placement`, `Fees`, `Event`, `Holiday`, `General`.
   - **`priority`**: `Low`, `Medium`, or `High` based on urgency.
   - **`deadline`**: ISO format (`YYYY-MM-DD`) if a due date is present, otherwise `null`.
3. **Resilience Guarantee**: If the AI API key is missing, network fails, or the AI times out, the backend automatically triggers a deterministic heuristic engine. **The notification is 100% guaranteed to be saved without throwing an error.**

---

## 📑 Frontend Integration API Contract

### Headers
For authenticated requests, include:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

### 1. Authentication Endpoints

#### `POST /api/auth/register`
Create a new student or admin account.
- **Auth**: None
- **Request Body**:
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@college.edu",
  "password": "Password123!",
  "role": "student"
}
```
*(role can be `"student"` or `"admin"`)*

- **Response (201 Created)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@college.edu",
    "role": "student",
    "created_at": "2026-09-19T10:00:00"
  }
}
```

---

#### `POST /api/auth/login`
Authenticate existing user. Accepts JSON body.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "jane.doe@college.edu",
  "password": "Password123!"
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@college.edu",
    "role": "student",
    "created_at": "2026-09-19T10:00:00"
  }
}
```

---

#### `GET /api/auth/me`
Retrieve logged-in user profile.
- **Auth**: Bearer Token
- **Response (200 OK)**:
```json
{
  "id": 1,
  "name": "Jane Doe",
  "email": "jane.doe@college.edu",
  "role": "student",
  "created_at": "2026-09-19T10:00:00"
}
```

---

### 2. Notifications Endpoints

#### `GET /api/notifications`
List notifications with optional filtering and search. Read status (`is_read`) is personalized for the requesting student.
- **Auth**: Bearer Token (Optional: defaults `is_read` to false if unauthenticated)
- **Query Parameters**:
  - `category`: Filter by category (e.g. `exam`, `placement`, `fees`)
  - `priority`: Filter by priority (`low`, `medium`, `high`)
  - `search`: Keyword search in title, summary, and content
  - `is_read`: Filter by read status (`true` or `false`)
  - `skip`: Pagination offset (default: 0)
  - `limit`: Pagination limit (default: 50, max: 100)

- **Examples**:
  - `GET /api/notifications?category=exam`
  - `GET /api/notifications?priority=high`
  - `GET /api/notifications?search=placement`
  - `GET /api/notifications?is_read=false`

- **Response (200 OK)**:
```json
[
  {
    "id": 101,
    "title": "Placement Training Registration",
    "summary": "Students must register for placement training before Friday.",
    "category": "Placement",
    "priority": "High",
    "deadline": "2026-09-25",
    "is_read": false,
    "created_at": "2026-09-19T10:00:00"
  }
]
```

---

#### `GET /api/notifications/{id}`
Retrieve a single notification's complete details.
- **Auth**: Bearer Token (Optional)
- **Response (200 OK)**:
```json
{
  "id": 101,
  "title": "Placement Training Registration",
  "summary": "Students must register for placement training before Friday.",
  "original_content": "All final year engineering students must register for the mandatory corporate placement training before Friday 2026-09-25. Late registrations will not be accommodated.",
  "category": "Placement",
  "priority": "High",
  "deadline": "2026-09-25",
  "is_read": false,
  "created_by": 1,
  "created_at": "2026-09-19T10:00:00",
  "updated_at": "2026-09-19T10:00:00"
}
```

---

#### `POST /api/notifications`
Create a new notification announcement.
- **Auth**: **Admin Only** (Bearer Token with `role: "admin"`)
- **Request Body**:
```json
{
  "title": "Placement Training Registration",
  "content": "All final year engineering students must register for corporate placement training before Friday 2026-09-25."
}
```
*(Optional fields: `category`, `priority`, `deadline` if the admin wishes to manually specify them instead of relying solely on AI)*

- **Response (201 Created)**:
```json
{
  "id": 101,
  "title": "Placement Training Registration",
  "summary": "Students must register for corporate placement training before Friday 2026-09-25.",
  "category": "Placement",
  "priority": "High",
  "deadline": "2026-09-25",
  "is_read": false,
  "created_at": "2026-09-19T10:00:00"
}
```

---

#### `PUT /api/notifications/{id}`
Update an existing notification.
- **Auth**: **Admin Only**
- **Request Body** (all fields optional):
```json
{
  "title": "Updated Placement Notice",
  "content": "Updated announcement text.",
  "category": "Placement",
  "priority": "High",
  "deadline": "2026-09-28",
  "rerun_ai": false
}
```
- **Response (200 OK)**: Returns updated `NotificationResponse`.

---

#### `DELETE /api/notifications/{id}`
Permanently delete a notification.
- **Auth**: **Admin Only**
- **Response (200 OK)**:
```json
{
  "message": "Notification 101 deleted successfully",
  "id": 101
}
```

---

#### `PUT /api/notifications/{id}/read`
Mark a notification as read for the logged-in student.
- **Auth**: Bearer Token
- **Response (200 OK)**:
```json
{
  "id": 101,
  "title": "Placement Training Registration",
  "summary": "Students must register for placement training before Friday.",
  "category": "Placement",
  "priority": "High",
  "deadline": "2026-09-25",
  "is_read": true,
  "created_at": "2026-09-19T10:00:00"
}
```

---

### 3. Admin Analytics & Management

#### `GET /api/admin/stats`
Get aggregated dashboard statistics.
- **Auth**: **Admin Only**
- **Response (200 OK)**:
```json
{
  "total_notifications": 42,
  "total_users": 150,
  "total_students": 145,
  "total_admins": 5,
  "total_reads": 380,
  "categories": {
    "Exam": 12,
    "Placement": 10,
    "Academic": 8,
    "Fees": 5,
    "Event": 4,
    "Holiday": 3
  },
  "priorities": {
    "High": 18,
    "Medium": 16,
    "Low": 8
  }
}
```

#### `GET /api/admin/users`
List registered users.
- **Auth**: **Admin Only**
- **Response (200 OK)**: List of `UserResponse` objects.

---

## 🔒 Security & CORS

- **CORS**: Configured with `CORSMiddleware`. Allowed origins default to `*` for easy frontend hackathon connection, or can be restricted in `.env`.
- **RBAC**: Protected routes strictly enforce student vs admin permissions (returns HTTP `403 Forbidden` if a student attempts admin operations).
- **Secrets**: Passwords hashed with `bcrypt`, JWT signed with `HS256`, secrets loaded via `.env`.
