from fastapi import APIRouter

from app.controller.v1 import v1_router

controller_router = APIRouter()

controller_router.include_router(v1_router, prefix="/v1")

