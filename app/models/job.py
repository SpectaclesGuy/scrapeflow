from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class Job(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    job_type: Mapped[str] = mapped_column(String(100), default="extraction", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="jobs")
    conversation = relationship("Conversation", back_populates="jobs")
