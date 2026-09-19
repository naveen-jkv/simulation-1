from app.routers.auth import router as auth_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import router as admin_router

__all__ = ["auth_router", "notifications_router", "admin_router"]
