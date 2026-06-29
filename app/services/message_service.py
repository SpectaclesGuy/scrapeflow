from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.message_schema import MessageCreate
from app.services.context_service import get_context, update_context_from_message


def create_message(db: Session, conversation_id: str, payload: MessageCreate) -> tuple[Message, object]:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ValueError("Conversation not found")

    message = Message(
        conversation_id=conversation_id,
        role=payload.role,
        content=payload.content,
        meta=payload.metadata,
    )
    db.add(message)

    project_context = get_context(db, conversation.project_id)
    if project_context is None:
        raise ValueError("Project context not found")

    update_context_from_message(project_context, payload.content)
    db.commit()
    db.refresh(message)
    db.refresh(project_context)
    return message, project_context


def list_messages(db: Session, conversation_id: str) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
