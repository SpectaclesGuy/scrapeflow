from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    PLANNER = "planner"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class ContextStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"


class JobStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
