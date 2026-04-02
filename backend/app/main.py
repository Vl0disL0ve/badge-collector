from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .core import config
from .api import (
    auth_router, categories_router, sets_router, badges_router,
    tags_router, admin_router, ml_router, export_router,
    similarity_router, telegram_router
)

app = FastAPI(title="Badge Collector API", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы (загрузки)
os.makedirs(config.settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.settings.UPLOAD_DIR), name="uploads")

# ========== ФРОНТЕНД ==========
# Определяем путь к корню фронтенда
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")

# Монтируем статические папки фронтенда
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_PATH, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_PATH, "js")), name="js")

# Монтируем HTML страницы по новым путям
app.mount("/html/auth", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html", "auth")), name="auth")
app.mount("/html/collection", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html", "collection")), name="collection")
app.mount("/html/badges", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html", "badges")), name="badges")
app.mount("/html/user", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html", "user")), name="user")

# Подключаем роутеры API
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(categories_router, prefix="/api", tags=["categories"])
app.include_router(sets_router, prefix="/api", tags=["sets"])
app.include_router(badges_router, prefix="/api", tags=["badges"])
app.include_router(tags_router, prefix="/api", tags=["tags"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(ml_router, prefix="/api", tags=["ml"])
app.include_router(export_router, prefix="/api", tags=["export"])
app.include_router(similarity_router, prefix="/api", tags=["similarity"])
app.include_router(telegram_router, prefix="/api", tags=["telegram"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "3.0.0"}


# Корневой маршрут — редирект на логин
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/html/auth/login.html")