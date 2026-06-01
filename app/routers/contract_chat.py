# app/routers/contract_chat.py

import json
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.openai_client import run_contract_chatbot_turn
from app.data.contract_schemas import CONTRACT_SCHEMAS


router = APIRouter(prefix="/api/contract-chat", tags=["Contract Chat"])


session_store: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str, request: Request) -> Dict[str, Any]:
    if session_id not in session_store:
        session_store[session_id] = {
            "session_id": session_id,

            # Main chatbot state
            "detected_contract_type": None,
            "collected_data": {},
            "last_requested_fields": [],
            "status": "initializing",

            # New incomplete-field confirmation state
            # These keys are used by run_contract_chatbot_turn in openai_client.py
            "awaiting_incomplete_fields_confirmation": False,
            "pending_incomplete_fields": [],
            "allow_generation_with_incomplete": False,

            # Legacy / old state keys.
            # Keeping them does not hurt, but the new openai_client.py does not rely on them.
            "pending_draft_confirmation": False,
            "pending_finalization_missing_fields": [],
            "last_missing_prompt": None,
        }

    else:
        # Defensive migration for old sessions that were created before the new keys existed.
        session = session_store[session_id]

        if "collected_data" not in session or not isinstance(session.get("collected_data"), dict):
            session["collected_data"] = {}

        if "last_requested_fields" not in session or not isinstance(session.get("last_requested_fields"), list):
            session["last_requested_fields"] = []

        if "status" not in session:
            session["status"] = "initializing"

        if "awaiting_incomplete_fields_confirmation" not in session:
            session["awaiting_incomplete_fields_confirmation"] = False

        if "pending_incomplete_fields" not in session or not isinstance(session.get("pending_incomplete_fields"), list):
            session["pending_incomplete_fields"] = []

        if "allow_generation_with_incomplete" not in session:
            session["allow_generation_with_incomplete"] = False

    return session_store[session_id]


def normalize_context(context: Any) -> str:
    """
    Frontend may send context as:
    - string
    - dict/object
    - list
    - None

    The AI service expects a string, so we normalize it here.
    """
    if context is None:
        return ""

    if isinstance(context, str):
        return context

    try:
        return json.dumps(context, ensure_ascii=False)
    except Exception:
        return str(context)


class ChatPayload(BaseModel):
    message: str
    session_id: str
    language: Optional[str] = "en"
    tone: Optional[str] = "professional"
    context: Optional[Any] = ""


class ChatResponse(BaseModel):
    reply: str
    draft: Optional[str] = None
    session_id: str
    session: Dict[str, Any]
    detected_contract_type: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    status: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatPayload, request: Request):
    session = get_session(payload.session_id, request)

    try:
        context_value = normalize_context(payload.context)

        result = await run_contract_chatbot_turn(
            user_message=payload.message,
            session=session,
            contract_schemas=CONTRACT_SCHEMAS,
            language=payload.language or "en",
            tone=payload.tone or "professional",
            context=context_value,
        )

        updated_session = result.get("session", session)
        updated_session["session_id"] = payload.session_id

        # Persist updated session.
        # This is important because run_contract_chatbot_turn updates:
        # - collected_data
        # - last_requested_fields
        # - awaiting_incomplete_fields_confirmation
        # - pending_incomplete_fields
        # - allow_generation_with_incomplete
        # - status
        session_store[payload.session_id] = updated_session

        return ChatResponse(
            reply=result.get("reply") or "",
            draft=result.get("draft"),
            session_id=payload.session_id,
            session=updated_session,
            detected_contract_type=result.get("detected_contract_type"),
            missing_fields=result.get("missing_fields", []),
            status=result.get("status") or updated_session.get("status", "unknown"),
        )

    except Exception as e:
        print(f"Error in contract chat endpoint: {e}")

        session["status"] = "error"
        session_store[payload.session_id] = session

        return ChatResponse(
            reply="I'm sorry, I encountered an internal error. Please try again.",
            draft=None,
            session_id=payload.session_id,
            session=session,
            detected_contract_type=session.get("detected_contract_type"),
            missing_fields=[],
            status="error",
        )
