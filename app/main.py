from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routes.context import router as context_router
from app.routes.conversations import router as conversations_router
from app.routes.jobs import router as jobs_router
from app.routes.projects import router as projects_router
from app.routes.users import router as users_router
from app.utils.response import error_response, success_response

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.detail)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response(str(exc)),
    )


@app.get("/health")
def health() -> dict:
    return success_response(
        "ScrapeFlow context service running",
        {"status": "ok"},
    )


app.include_router(users_router)
app.include_router(projects_router)
app.include_router(conversations_router)
app.include_router(context_router)
app.include_router(jobs_router)
