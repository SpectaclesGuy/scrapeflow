from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    user = relationship("User", back_populates="projects")
    conversations = relationship(
        "Conversation", back_populates="project", cascade="all, delete-orphan"
    )
    context = relationship(
        "ProjectContext", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
