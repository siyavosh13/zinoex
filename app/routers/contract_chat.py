from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user

from app.models.contract_chat_session import ContractChatSession
from app.schemas.contract_chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionDataResponse,
)

from app.services.contract_chat_intelligence import ContractChatIntelligence
from app.services.contract_chat_drafting import ContractChatDrafting


router = APIRouter(prefix="/api/contracts/chat", tags=["Contract Chat"])

intelligence_service = ContractChatIntelligence()
drafting_service = ContractChatDrafting()


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = None

    if payload.session_id:
        result = await db.execute(
            select(ContractChatSession).where(
                ContractChatSession.session_id == payload.session_id,
                ContractChatSession.user_id == current_user.id
            )
        )

        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

    if not session:
        session = ContractChatSession(
            session_id=str(uuid4()),
            user_id=current_user.id,
            status="collecting_info",
            conversation=[],
            collected_data={}
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

    conversation = list(session.conversation or [])

    conversation.append({
        "role": "user",
        "content": payload.message,
        "created_at": datetime.utcnow().isoformat()
    })

    session.conversation = conversation

    analysis = intelligence_service.analyze_message(
        message=payload.message,
        conversation=conversation,
        collected_data=session.collected_data or {},
        current_contract_type=session.detected_contract_type
    )

    if analysis.get("intent") == "out_of_scope":
        conversation.append({
            "role": "assistant",
            "content": analysis.get("reply"),
            "created_at": datetime.utcnow().isoformat()
        })

        session.conversation = conversation
        session.status = "out_of_scope"

        await db.commit()

        return ChatMessageResponse(
            session_id=session.session_id,
            reply=analysis.get("reply"),
            detected_intent="out_of_scope",
            detected_contract_type=session.detected_contract_type,
            needs_more_info=False,
            missing_fields=[],
            status="out_of_scope",
            extracted_data=session.collected_data or {}
        )

    merged_data = intelligence_service.merge_collected_data(
        existing_data=session.collected_data or {},
        extracted_data=analysis.get("extracted_data", {})
    )

    session.collected_data = merged_data

    if analysis.get("contract_type"):
        session.detected_contract_type = analysis.get("contract_type")

    if analysis.get("ready_to_draft"):
        draft = drafting_service.generate_draft(
            contract_type=session.detected_contract_type or "general",
            collected_data=merged_data
        )

        conversation.append({
            "role": "assistant",
            "content": draft,
            "created_at": datetime.utcnow().isoformat()
        })

        session.conversation = conversation
        session.status = "completed"

        await db.commit()

        return ChatMessageResponse(
            session_id=session.session_id,
            reply=draft,
            detected_intent=analysis.get("intent"),
            detected_contract_type=session.detected_contract_type,
            needs_more_info=False,
            missing_fields=[],
            status="completed",
            extracted_data=merged_data
        )

    reply = analysis.get(
        "reply",
        "Please provide more details about the contract."
    )

    conversation.append({
        "role": "assistant",
        "content": reply,
        "created_at": datetime.utcnow().isoformat()
    })

    session.conversation = conversation
    session.status = "collecting_info"

    await db.commit()

    return ChatMessageResponse(
        session_id=session.session_id,
        reply=reply,
        detected_intent=analysis.get("intent"),
        detected_contract_type=session.detected_contract_type,
        needs_more_info=True,
        missing_fields=analysis.get("missing_fields", []),
        status="collecting_info",
        extracted_data=merged_data
    )


@router.get("/session/{session_id}", response_model=ChatSessionDataResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ContractChatSession).where(
            ContractChatSession.session_id == session_id,
            ContractChatSession.user_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ChatSessionDataResponse(
        session_id=session.session_id,
        status=session.status,
        detected_contract_type=session.detected_contract_type,
        collected_data=session.collected_data or {},
        conversation=session.conversation or []
    )


@router.get("/sessions/me")
async def my_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ContractChatSession)
        .where(ContractChatSession.user_id == current_user.id)
        .order_by(desc(ContractChatSession.updated_at))
    )

    sessions = result.scalars().all()

    return [
        {
            "session_id": session.session_id,
            "status": session.status,
            "detected_contract_type": session.detected_contract_type,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        }
        for session in sessions
    ]
