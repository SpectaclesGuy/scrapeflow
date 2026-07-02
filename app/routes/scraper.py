from fastapi import APIRouter

from app.schemas.scrape_schema import ScrapeRunRequest
from app.services.scraper_service import run_scrape_job
from app.utils.response import success_response

router = APIRouter(tags=['scraper'])


@router.post('/scrape/run')
async def scrape_run_route(payload: ScrapeRunRequest) -> dict:
    summary = await run_scrape_job(payload.config)
    return success_response('Scrape run completed', summary.model_dump())
