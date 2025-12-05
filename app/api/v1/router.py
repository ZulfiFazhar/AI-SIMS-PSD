from fastapi import APIRouter
from app.api.v1.routes import ping_route

router_v1 = APIRouter()

router_v1.include_router(ping_route.router)