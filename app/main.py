import asyncio
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.routes.auth import router as auth_router
from app.routes.context import router as context_router
from app.routes.conversations import router as conversations_router
from app.routes.jobs import router as jobs_router
from app.routes.projects import router as projects_router
from app.routes.scraper import router as scraper_router
from app.routes.users import router as users_router
from app.utils.response import error_response, success_response

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

settings = get_settings()
logger = logging.getLogger(__name__)
base_dir = Path(__file__).resolve().parent.parent
frontend_dir = Path(__file__).parent / 'ui' / 'scrapeflow-ui'
frontend_pages = {
    'login',
    'signup',
    'dashboard',
    'projects',
    'project',
    'chat',
    'context',
    'plan',
    'jobs',
    'job',
    'results',
    'exports',
    'settings',
}


def run_startup_migrations() -> None:
    alembic_config = Config(str(base_dir / 'alembic.ini'))
    alembic_config.set_main_option('script_location', str(base_dir / 'alembic'))
    alembic_config.set_main_option('sqlalchemy.url', settings.database_url)
    command.upgrade(alembic_config, 'head')
    logger.info('Database migrations applied successfully')


app = FastAPI(title=settings.app_name)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie_name,
    same_site='lax',
    https_only=settings.session_https_only,
    max_age=settings.session_max_age,
)
app.mount('/ui', StaticFiles(directory=frontend_dir), name='ui')


@app.on_event('startup')
def apply_database_migrations() -> None:
    if not settings.run_startup_migrations:
        logger.info('Startup migrations disabled; set RUN_STARTUP_MIGRATIONS=true to enable them.')
        return
    run_startup_migrations()


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


@app.get('/health')
def health() -> dict:
    return success_response(
        'ScrapeFlow scraper service running',
        {'status': 'ok'},
    )


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(conversations_router)
app.include_router(context_router)
app.include_router(jobs_router)
app.include_router(scraper_router)


@app.get('/{page_name}.html', include_in_schema=False)
def html_redirect(page_name: str):
    if page_name not in frontend_pages:
        raise HTTPException(status_code=404, detail='Page not found')
    return RedirectResponse(url=f'/{page_name}', status_code=307)


@app.get('/{page_name}', include_in_schema=False)
def clean_html_page(page_name: str) -> FileResponse:
    if page_name not in frontend_pages:
        raise HTTPException(status_code=404, detail='Page not found')
    return FileResponse(frontend_dir / f'{page_name}.html')
