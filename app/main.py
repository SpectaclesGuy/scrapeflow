from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes.context import router as context_router
from app.routes.conversations import router as conversations_router
from app.routes.jobs import router as jobs_router
from app.routes.projects import router as projects_router
from app.routes.scraper import router as scraper_router
from app.routes.users import router as users_router
from app.utils.response import error_response, success_response

settings = get_settings()
app = FastAPI(title=settings.app_name)
frontend_dir = Path(__file__).parent / 'ui' / 'scrapeflow-ui'
app.mount('/ui', StaticFiles(directory=frontend_dir), name='ui')


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


@app.get('/', include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(frontend_dir / 'index.html')


@app.get('/{page_name}.html', include_in_schema=False)
def html_page(page_name: str) -> FileResponse:
    target = frontend_dir / f'{page_name}.html'
    if not target.exists():
        raise HTTPException(status_code=404, detail='Page not found')
    return FileResponse(target)


@app.get('/health')
def health() -> dict:
    return success_response(
        'ScrapeFlow scraper service running',
        {'status': 'ok'},
    )


app.include_router(users_router)
app.include_router(projects_router)
app.include_router(conversations_router)
app.include_router(context_router)
app.include_router(jobs_router)
app.include_router(scraper_router)
