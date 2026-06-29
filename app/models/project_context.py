from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class ProjectContext(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_context"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"), nullable=False, unique=True, index=True
    )
    target_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    filters: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    pagination: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    export_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    schedule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project = relationship("Project", back_populates="context")
