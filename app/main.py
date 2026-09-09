from fastapi import FastAPI

from app.clubs.router import router as clubs_router
from app.config import get_settings
from app.events.router import router as events_router
from app.health.router import router as health_router
from app.users.router import router as users_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(users_router)
app.include_router(clubs_router)
app.include_router(events_router)
