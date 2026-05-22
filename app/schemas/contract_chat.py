from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class ChatMessageRequest(BaseModel):

    session_id: Optional[str] = None

    message: str = Field(..., min_length=1)

    language: Optional[str] = "English"


class ChatMessageResponse(BaseModel):

    session_id: str

    reply: str

    detected_intent: Optional[str] = None

    detected_contract_type: Optional[str] = None

    needs_more_info: bool = False

    missing_fields: List[str] = Field(default_factory=list)

    status: Literal[
        "collecting_info",
        "completed",
        "out_of_scope"
    ]

    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class ChatSessionDataResponse(BaseModel):

    session_id: str

    status: str

    detected_contract_type: Optional[str] = None

    collected_data: Dict[str, Any] = Field(default_factory=dict)

    conversation: List[Dict[str, Any]] = Field(default_factory=list)
