from fastapi import APIRouter
from app.api.routes import auth_route

router_v1 = APIRouter()

router_v1.include_router(auth_route.router)
