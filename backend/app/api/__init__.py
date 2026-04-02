from .auth import router as auth_router
from .categories import router as categories_router
from .sets import router as sets_router
from .badges import router as badges_router
from .tags import router as tags_router
from .admin import router as admin_router
from .ml import router as ml_router
from .export import router as export_router
from .similarity import router as similarity_router
from .telegram import router as telegram_router

__all__ = [
    "auth_router",
    "categories_router",
    "sets_router",
    "badges_router",
    "tags_router",
    "admin_router",
    "ml_router",
    "export_router",
    "similarity_router",
    "telegram_router"
]