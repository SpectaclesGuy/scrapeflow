import json
from pathlib import Path

from app.config import get_settings
from app.schemas.scrape_schema import ScrapeJobConfig
from app.services.extraction_service import detect_failed_fields, extract_records_from_html
from app.services.preprocessing_service import preprocess_html_for_slm
from app.services.schema_alignment_service import normalize_records_with_slm
from app.services.scraper_service import run_scrape_job, should_use_browser
from app.services.selector_repair_service import repair_failed_selectors
from app.services.storage_service import save_csv, save_evidence, save_json

SAMPLE_HTML = """
<html>
  <head>
    <script>large tracking script</script>
    <style>.x{}</style>
  </head>
  <body>
    <nav>navigation</nav>
    <div class="product-card">
      <h2 class="product-title">Laptop A</h2>
      <span class="wrong-price-class">?50,000</span>
      <span class="rating">4.5</span>
    </div>
    <footer>footer</footer>
  </body>
</html>
"""


def build_config(project_id: str | None = 'project_001') -> ScrapeJobConfig:
    return ScrapeJobConfig.model_validate(
        {
            'job_id': 'job_001',
            'project_id': project_id,
            'target_url': 'https://example.com/products',
            'mode': 'http',
            'entity': 'product',
            'container_selector': '.product-card',
            'fields': [
                {'name': 'title', 'selector': '.product-title', 'type': 'text', 'required': True},
                {'name': 'price', 'selector': '.price', 'type': 'text', 'required': True},
                {'name': 'rating', 'selector': '.rating', 'type': 'text', 'required': False},
            ],
            'pagination': {'enabled': False, 'type': 'none', 'max_pages': 1},
            'browser': {'headless': True, 'wait_until': 'networkidle', 'timeout': 30000},
            'slm': {'enabled': True, 'provider': 'mock', 'model': 'mock-scrapeflow-slm', 'max_input_chars': 12000},
            'output': {'formats': ['json', 'csv'], 'include_evidence': True},
        }
    )



def test_extract_records_and_detect_failed_fields():
    config = build_config()
    records = extract_records_from_html(SAMPLE_HTML, config, 'https://example.com/products', 1)
    assert records[0]['data']['title'] == 'Laptop A'
    assert records[0]['data']['price'] == ''
    failed = detect_failed_fields(records[0], config)
    assert failed == ['price']



def test_preprocess_html_removes_noise():
    config = build_config()
    cleaned = preprocess_html_for_slm(SAMPLE_HTML, config, ['price'])
    assert 'tracking script' not in cleaned
    assert 'navigation' not in cleaned
    assert 'footer' not in cleaned
    assert 'wrong-price-class' in cleaned



def test_selector_repair_flow_recovers_price():
    config = build_config()
    repair = __import__('asyncio').run(repair_failed_selectors(SAMPLE_HTML, config, ['price']))
    assert repair['suggested_selectors']['price'] == '.wrong-price-class'
    assert repair['recovered_values']['price']['value'] == '?50,000'



def test_storage_outputs(tmp_path, monkeypatch):
    monkeypatch.setenv('OUTPUT_DIR', str(tmp_path))
    get_settings.cache_clear()
    records = [{'data': {'title': 'Laptop A', 'price': '?50,000'}, 'evidence': {'price': {'field': 'price'}}, 'warnings': []}]
    json_path = save_json('job_storage', records)
    csv_path = save_csv('job_storage', records)
    evidence_path = save_evidence('job_storage', records)
    assert Path(json_path).exists()
    assert Path(csv_path).exists()
    assert Path(evidence_path).exists()



def test_normalize_records_with_slm():
    records = [{'data': {'rating': '4', 'title': 'Laptop A'}, 'evidence': {}, 'warnings': []}]
    normalized = __import__('asyncio').run(normalize_records_with_slm(records, {'rating': 'int', 'title': 'string'}))
    assert normalized[0]['data']['rating'] == 4



def test_should_use_browser_heuristics():
    config = build_config()
    html = '<html><body><div id="root"></div><script></script></body></html>'
    assert should_use_browser(html, config) is True



def test_run_scrape_job_with_mock_fetch(monkeypatch, tmp_path):
    monkeypatch.setenv('OUTPUT_DIR', str(tmp_path))
    get_settings.cache_clear()

    async def fake_fetch_html(url: str, timeout: int = 30) -> str:
        return SAMPLE_HTML

    monkeypatch.setattr('app.services.scraper_service.fetch_html', fake_fetch_html)
    config = build_config()
    summary = __import__('asyncio').run(run_scrape_job(config))
    assert summary.status == 'completed'
    assert summary.records_found == 1
    assert summary.records[0].data['price'] == '?50,000'
    assert 'json' in summary.output_paths



def test_scrape_run_endpoint(client, monkeypatch, tmp_path):
    monkeypatch.setenv('OUTPUT_DIR', str(tmp_path))
    get_settings.cache_clear()

    async def fake_fetch_html(url: str, timeout: int = 30) -> str:
        return SAMPLE_HTML

    monkeypatch.setattr('app.services.scraper_service.fetch_html', fake_fetch_html)
    response = client.post('/scrape/run', json={'config': build_config().model_dump()})
    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['status'] == 'completed'
    assert payload['records_found'] == 1



def test_job_run_and_results_endpoint(client, monkeypatch, tmp_path):
    monkeypatch.setenv('OUTPUT_DIR', str(tmp_path))
    get_settings.cache_clear()
    user = client.post('/users', json={'name': 'Mayank', 'email': 'jobs@example.com', 'password_hash': 'hashed'}).json()['data']
    project = client.post(
        '/projects',
        json={'user_id': user['id'], 'name': 'Laptop Scraper', 'description': 'Collect listings'},
    ).json()['data']

    async def fake_fetch_html(url: str, timeout: int = 30) -> str:
        return SAMPLE_HTML

    monkeypatch.setattr('app.services.scraper_service.fetch_html', fake_fetch_html)
    config = build_config(project['id']).model_dump()
    create_response = client.post('/jobs', json={'project_id': project['id'], 'job_type': 'scrape', 'config': config})
    job_id = create_response.json()['data']['id']

    run_response = client.post(f'/jobs/{job_id}/run')
    assert run_response.status_code == 200
    run_payload = run_response.json()['data']
    assert run_payload['status'] == 'completed'
    assert run_payload['records'][0]['data']['price'] == '?50,000'

    results_response = client.get(f'/jobs/{job_id}/results')
    assert results_response.status_code == 200
    results = results_response.json()['data']
    assert results['status'] == 'completed'
    assert results['records'][0]['data']['title'] == 'Laptop A'
