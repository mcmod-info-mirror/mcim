from fastapi import FastAPI, BackgroundTasks, Body, status, APIRouter
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi.openapi.docs import (
    get_swagger_ui_html,
)
from fastapi.staticfiles import StaticFiles

docs_router = APIRouter(prefix="/docs", include_in_schema=False)


@docs_router.get("docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f'/openapi.json',
        title="MCIM - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )