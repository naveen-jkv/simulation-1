import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import engine, Base
import app.models  # Ensures models are imported for metadata
from app.routers import auth_router, notifications_router, admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Automatically creates database tables on startup if they do not already exist.
    """
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("Application shutting down.")


# Define OpenAPI tags for rich Swagger documentation
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, JWT token issuance, and user profile retrieval.",
    },
    {
        "name": "Notifications",
        "description": "Notification CRUD operations, AI content summarization, classification, deadline detection, search, and student read tracking.",
    },
    {
        "name": "Admin Operations",
        "description": "Administrative metrics, system stats, and user directory inspection.",
    },
]

app = FastAPI(
    title="AI College Notification Hub API",
    description=(
        "Production-grade backend REST API for college announcements and notifications. "
        "Empowered by OpenAI-compatible AI for auto-summarization, intelligent taxonomy classification, "
        "deadline extraction, and priority assignment with deterministic fallback resilience."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend integration
origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation error handler for friendly JSON responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({"field": field, "message": err.get("msg")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Request body or parameters failed validation.",
            "issues": errors,
        },
    )


# Include Routers
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(admin_router)


@app.get(
    "/",
    tags=["Health"],
    summary="Root Health Check",
    description="Returns backend API operational status and documentation links.",
)
def root():
    return {
        "status": "online",
        "service": "AI College Notification Hub Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness and Readiness Probe",
)
def health():
    return {"status": "healthy"}
