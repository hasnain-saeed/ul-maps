from fastapi import APIRouter
from api.v1.endpoints import routes, realtime, health

api_router = APIRouter()
api_router.include_router(routes.router, tags=["routes"])
api_router.include_router(realtime.router, tags=["realtime"])
api_router.include_router(health.router, tags=["health"])
