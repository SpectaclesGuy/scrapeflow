from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import Conversation
from app.models.project import Project
from app.schemas.context_schema import ProjectContextRead
from app.schemas.conversation_schema import ConversationCreate, ConversationRead
from app.schemas.message_schema import MessageCreate, MessageRead
from app.services.context_service import get_context
from app.services.message_service import create_message, list_messages
from app.utils.response import success_response

router = APIRouter(tags=['conversations'])


@router.post('/conversations')
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> dict:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    conversation = Conversation(**payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return success_response(
        'Conversation created successfully',
        ConversationRead.model_validate(conversation).model_dump(),
    )


@router.get('/conversations/{conversation_id}')
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> dict:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')
    return success_response(
        'Conversation fetched successfully',
        ConversationRead.model_validate(conversation).model_dump(),
    )


@router.get('/projects/{project_id}/conversations')
def list_conversations(project_id: str, db: Session = Depends(get_db)) -> dict:
    conversations = (
        db.query(Conversation)
        .filter(Conversation.project_id == project_id)
        .order_by(Conversation.created_at)
        .all()
    )
    data = [ConversationRead.model_validate(item).model_dump() for item in conversations]
    return success_response('Conversations fetched successfully', data)


@router.post('/conversations/{conversation_id}/messages')
def create_message_route(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)) -> dict:
    try:
        message, context = create_message(db, conversation_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if context is None:
        conversation = db.get(Conversation, conversation_id)
        context = get_context(db, conversation.project_id) if conversation else None
    return success_response(
        'Message stored and context updated successfully',
        {
            'message': MessageRead.model_validate(message).model_dump(),
            'context': ProjectContextRead.model_validate(context).model_dump() if context else None,
        },
    )


@router.get('/conversations/{conversation_id}/messages')
def list_messages_route(conversation_id: str, db: Session = Depends(get_db)) -> dict:
    messages = [MessageRead.model_validate(item).model_dump() for item in list_messages(db, conversation_id)]
    return success_response('Messages fetched successfully', messages)
