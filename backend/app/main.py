from fastapi import FastAPI

from app.api.middleware import RequestContextMiddleware
from app.api.routes.document import router as document_router
from app.api.routes.health import router as health_router
from app.api.routes.source import router as source_router
from app.api.routes.workflow import router as workflow_router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging(settings.log_level)

app = FastAPI(
    title="Insight Flow API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(source_router)
app.include_router(document_router)
app.include_router(workflow_router)
