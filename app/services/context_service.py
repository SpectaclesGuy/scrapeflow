import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.project_context import ProjectContext
from app.schemas.context_schema import ProjectContextUpdate

URL_PATTERN = re.compile(r"(https?://[^\s]+)")
FORMAT_PATTERN = re.compile(r"\b(excel|csv|json)\b", re.IGNORECASE)
FIELD_PATTERN = re.compile(
    r"(?:include|add|also include)\s+([a-z0-9_\-\s,]+?)(?:\b(?:and export|export|with|where|that|for)\b|$)",
    re.IGNORECASE,
)
EXTRACT_FIELD_PATTERN = re.compile(
    r"\bextract\s+([a-z0-9_\-]+)(?:\s*(?:,|and|$))",
    re.IGNORECASE,
)
FILTER_PATTERN = re.compile(
    r"\b([a-z0-9_\-\s]+?)\s+(above|below|greater than|less than|under|over|minimum|maximum)\s+([a-z0-9_\-\s]+)",
    re.IGNORECASE,
)
ENTITY_PATTERN = re.compile(
    r"\b(?:extract|scrape|get|find)\s+([a-z][a-z0-9_\-\s]+?)(?:\s+from|\s+with|\s+where|\s+that|\s*$)",
    re.IGNORECASE,
)
STOPWORDS = {"and", "the", "a", "an", "all", "also", "include", "extract", "add"}


def get_context(db: Session, project_id: str) -> ProjectContext | None:
    return (
        db.query(ProjectContext)
        .filter(ProjectContext.project_id == project_id)
        .one_or_none()
    )


def replace_context(
    db: Session, project_context: ProjectContext, payload: ProjectContextUpdate
) -> ProjectContext:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project_context, field, value)
    db.commit()
    db.refresh(project_context)
    return project_context


def patch_context(
    db: Session, project_context: ProjectContext, payload: ProjectContextUpdate
) -> ProjectContext:
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in data.items():
        setattr(project_context, field, value)
    db.commit()
    db.refresh(project_context)
    return project_context


def update_context_from_message(project_context: ProjectContext, message: str) -> ProjectContext:
    """
    Rule-based temporary context updater.
    Later this can be replaced by Planner Agent / LLM integration.
    """
    text = message.strip()
    if not text:
        project_context.version += 1
        return project_context

    url_match = URL_PATTERN.search(text)
    if url_match:
        target_url = url_match.group(1).rstrip(".,)")
        project_context.target_url = target_url
        parsed = urlparse(target_url)
        project_context.domain = parsed.netloc or project_context.domain

    format_match = FORMAT_PATTERN.search(text)
    if format_match:
        project_context.export_format = format_match.group(1).lower()

    fields = list(project_context.fields or [])
    for match in FIELD_PATTERN.finditer(text):
        phrase = match.group(1)
        for raw_field in re.split(r",| and ", phrase):
            field = normalize_token(raw_field)
            if field and field not in fields:
                fields.append(field)
    for match in EXTRACT_FIELD_PATTERN.finditer(text):
        field = normalize_token(match.group(1))
        if field and field not in fields:
            fields.append(field)
    project_context.fields = fields

    filters = list(project_context.filters or [])
    for match in FILTER_PATTERN.finditer(text):
        field = normalize_token(match.group(1))
        operator = match.group(2).lower()
        value = match.group(3).strip()
        candidate = {"field": field, "operator": operator, "value": value}
        if field and candidate not in filters:
            filters.append(candidate)
    project_context.filters = filters

    if not project_context.entity:
        entity_match = ENTITY_PATTERN.search(text)
        if entity_match:
            project_context.entity = normalize_entity(entity_match.group(1))

    project_context.version += 1
    return project_context


def normalize_token(value: str) -> str | None:
    token = re.sub(r"[^a-z0-9_\-\s]", " ", value.lower())
    token = " ".join(part for part in token.split() if part not in STOPWORDS)
    return token or None


def normalize_entity(value: str) -> str | None:
    entity = normalize_token(value)
    if not entity:
        return None
    words = entity.split()
    return " ".join(words[:3])
