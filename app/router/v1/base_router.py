from fastapi import APIRouter

from app.router.v1.router_v1__code_review import path_code_review

routers = APIRouter()
router_list = [path_code_review]

for router in router_list:
    router.tags = routers.tags.append("api/v1")
    routers.include_router(router)
