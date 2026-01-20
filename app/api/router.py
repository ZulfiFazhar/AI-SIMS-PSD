from fastapi import APIRouter
from app.api.routes import auth_route, tenant_route, proposal_route

router_v1 = APIRouter()

router_v1.include_router(auth_route.router)
router_v1.include_router(tenant_route.router)
router_v1.include_router(proposal_route.router)
