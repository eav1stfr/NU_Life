from fastapi import FastAPI

from app.config import get_settings
from app.health.router import router as health_router
from app.users.router import router as users_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(users_router)
