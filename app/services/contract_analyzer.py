# app/services/contract_analyzer.py

import json
import re
from typing import Any

from app.services.openai_client import call_openai_api
from app.data.contract_schemas import CONTRACT_SCHEMAS, get_valid_contract_types


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

ALLOWED_INTENTS = {
    "start_contract",
    "provide_info",
    "ask_question",
    "request_draft",
    "confirm_generate",
    "fill_missing",
    "skip_field",
    "unclear",
}

TBD_VALUE = "TBD"

TBD_LIKE_VALUES = {
    "tbd",
    "to be determined",
    "to be decided",
    "unknown",
    "not sure",
    "unsure",
    "n/a",
    "na",
    "not applicable",
    "not provided",
    "leave blank",
    "leave it blank",
    "skip",
    "skipped",
}


# ---------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_empty_value(value: Any) -> bool:
    """
    True only for actually missing/empty values.
    Important:
    - "TBD" is NOT empty.
    - "unknown" stored intentionally is NOT empty for missing calculation.
    """
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0

    return False


def is_tbd_value(value: Any) -> bool:
    """
    Detects placeholder / incomplete values.
    These should be treated as incomplete, not missing.
    """
    if value is None:
        return False

    if not isinstance(value, str):
        return False

    normalized = value.strip().lower()
    if normalized in TBD_LIKE_VALUES:
        return True

    # Also catch bracket placeholders like [insert date], [party name], etc.
    if normalized.startswith("[") and normalized.endswith("]"):
        return True

    return False


def is_meaningful_value(value: Any) -> bool:
    """
    Meaningful means present and not empty.
    TBD is considered present, but incomplete.
    """
    return not is_empty_value(value)


def looks_like_skip_request(user_message: str) -> bool:
    """
    Deterministic skip/TBD detection.
    This prevents the model from missing simple skip commands and causing loops.
    """
    text = normalize_text(user_message).lower()
    if not text:
        return False

    exact_phrases = {
        "skip",
        "skip it",
        "skip this",
        "skip this field",
        "leave it",
        "leave it blank",
        "leave blank",
        "blank",
        "tbd",
        "mark as tbd",
        "put tbd",
        "use tbd",
        "not sure",
        "i am not sure",
        "i'm not sure",
        "i dont know",
        "i don't know",
        "unknown",
        "not known",
        "later",
        "fill later",
        "i will provide later",
        "provide later",
        "not applicable",
        "n/a",
        "na",
    }

    if text in exact_phrases:
        return True

    patterns = [
        r"\bskip\b",
        r"\btbd\b",
        r"\bto be determined\b",
        r"\bto be decided\b",
        r"\bleave (it )?blank\b",
        r"\bnot sure\b",
        r"\bunsure\b",
        r"\bdon'?t know\b",
        r"\bprovide (it )?later\b",
        r"\bfill (it )?later\b",
        r"\bnot applicable\b",
        r"\bn/a\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        if result < 0:
            return 0.0
        if result > 1:
            return 1.0
        return result
    except Exception:
        return default


def get_schema_fields(contract_type: str | None) -> set[str]:
    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return set()

    schema = CONTRACT_SCHEMAS[contract_type]
    return set(schema.get("required_fields", []) + schema.get("optional_fields", []))


def get_required_fields(contract_type: str | None) -> list[str]:
    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return []

    schema = CONTRACT_SCHEMAS[contract_type]
    return list(schema.get("required_fields", []))


def filter_fields_for_schema(contract_type: str | None, fields: list[Any]) -> list[str]:
    """
    Keeps only fields that exist in the selected contract schema.
    """
    if not fields:
        return []

    allowed_fields = get_schema_fields(contract_type)
    if not allowed_fields:
        return []

    cleaned = []
    for field in fields:
        field_name = normalize_text(field)
        if field_name and field_name in allowed_fields and field_name not in cleaned:
            cleaned.append(field_name)

    return cleaned


# ---------------------------------------------------------------------
# Analyzer normalization
# ---------------------------------------------------------------------

def normalize_analysis_result(raw_result: Any, session: dict, user_message: str) -> dict:
    """
    Makes the OpenAI analyzer result predictable and compatible with the newer
    orchestration/state-machine logic.
    """
    if not isinstance(raw_result, dict):
        raw_result = {}

    intent = raw_result.get("intent") or "unclear"
    if intent not in ALLOWED_INTENTS:
        intent = "unclear"

    contract_type = raw_result.get("contract_type")
    if contract_type not in get_valid_contract_types():
        contract_type = None

    confidence = safe_float(raw_result.get("confidence", 0.0), 0.0)

    extracted_data = raw_result.get("extracted_data") or {}
    if not isinstance(extracted_data, dict):
        extracted_data = {}

    fields_to_mark_tbd = raw_result.get("fields_to_mark_tbd") or []
    if not isinstance(fields_to_mark_tbd, list):
        fields_to_mark_tbd = []

    assistant_reply = raw_result.get("assistant_reply") or ""
    if not isinstance(assistant_reply, str):
        assistant_reply = ""

    # If the user clearly asked to skip, force intent and map skip to last_requested_fields.
    # This is the important anti-loop fallback.
    if looks_like_skip_request(user_message):
        intent = "skip_field"

        last_requested_fields = session.get("last_requested_fields") or []
        if isinstance(last_requested_fields, str):
            last_requested_fields = [last_requested_fields]

        for field in last_requested_fields:
            field_name = normalize_text(field)
            if field_name and field_name not in fields_to_mark_tbd:
                fields_to_mark_tbd.append(field_name)

    # If there is already a session contract type, prefer it when model is uncertain.
    session_contract_type = session.get("detected_contract_type")
    valid_types = get_valid_contract_types()

    if session_contract_type in valid_types:
        if not contract_type:
            contract_type = session_contract_type
        elif contract_type != session_contract_type and confidence < 0.75:
            contract_type = session_contract_type

    # Filter extracted_data to schema fields only.
    extracted_data = filter_extracted_data(contract_type, extracted_data)

    # Filter fields_to_mark_tbd to schema fields only.
    fields_to_mark_tbd = filter_fields_for_schema(contract_type, fields_to_mark_tbd)

    # Do not allow empty values in extracted_data, but allow TBD if intentionally supplied.
    cleaned_extracted_data = {}
    for key, value in extracted_data.items():
        if is_empty_value(value):
            continue
        cleaned_extracted_data[key] = value

    return {
        "intent": intent,
        "contract_type": contract_type,
        "confidence": confidence,
        "extracted_data": cleaned_extracted_data,
        "fields_to_mark_tbd": fields_to_mark_tbd,

        # Kept for backward compatibility.
        # Recommendation: do not use this as the final chatbot reply if
        # openai_client.py/run_contract_chatbot_turn builds the final response.
        "assistant_reply": assistant_reply,
    }


# ---------------------------------------------------------------------
# Main OpenAI analyzer
# ---------------------------------------------------------------------

async def analyze_contract_chat_with_openai(
    user_message: str,
    session: dict
) -> dict:
    """
    Analyzes the user's message using OpenAI to determine intent, contract type,
    and extract relevant data.

    Important:
    - This analyzer should not be the final conversation orchestrator.
    - It should provide structured intent/extraction only.
    - Final reply and next-question logic should preferably remain in openai_client.py.
    """

    session = session or {}

    system_prompt = """
You are an AI analyzer for a contract-generation website.

Your job is to analyze the user's message and return structured JSON only.
You are NOT the final conversation orchestrator.

Core goals:
- Identify the user's intent.
- Identify the contract type only from CONTRACT_SCHEMAS.
- Extract field values into extracted_data.
- Identify fields the user wants to skip or mark as TBD.

Critical rules:
- All output must be valid JSON.
- All communication/content must be in English.
- ONLY use contract types listed in CONTRACT_SCHEMAS. Do not invent new contract types.
- If the contract type is ambiguous or not clearly identified, set "contract_type" to null.
- If the user provides data for fields, extract it accurately into "extracted_data".
- If the user says "skip", "TBD", "not sure", "leave it blank", "I don't know", "provide later", or similar,
  set intent to "skip_field" and add the relevant field to "fields_to_mark_tbd".
- If the user is skipping the currently requested field, use CURRENT_SESSION.last_requested_fields.
- A field marked as TBD is incomplete, but it is NOT missing.
- Do not ask the same skipped question again.
- Do not overwrite already collected valid data unless the user clearly corrects it.
- The "intent" must be one of:
  "start_contract", "provide_info", "ask_question", "request_draft",
  "confirm_generate", "fill_missing", "skip_field", "unclear".
- "assistant_reply" is kept only for backward compatibility. Keep it short.
- Prefer returning structured data over writing long assistant replies.
"""

    current_session_for_prompt = {
        "detected_contract_type": session.get("detected_contract_type"),
        "collected_data": session.get("collected_data", {}),
        "last_requested_fields": session.get("last_requested_fields", []),
        "status": session.get("status"),

        # New anti-loop / incomplete-field state
        "pending_incomplete_fields": session.get("pending_incomplete_fields", []),
        "awaiting_incomplete_fields_confirmation": session.get(
            "awaiting_incomplete_fields_confirmation",
            False,
        ),
        "allow_generation_with_incomplete": session.get(
            "allow_generation_with_incomplete",
            False,
        ),

        # Legacy compatibility state, if present
        "pending_draft_confirmation": session.get("pending_draft_confirmation", False),
        "pending_finalization_missing_fields": session.get(
            "pending_finalization_missing_fields",
            [],
        ),
        "last_missing_prompt": session.get("last_missing_prompt"),
    }

    user_prompt_content = f"""
CONTRACT_SCHEMAS:
{json.dumps(CONTRACT_SCHEMAS, ensure_ascii=False, indent=2)}

CURRENT_SESSION:
{json.dumps(current_session_for_prompt, ensure_ascii=False, indent=2)}

USER_MESSAGE:
{user_message}

Return a JSON object with exactly this structure:
{{
  "intent": "string",
  "contract_type": "string or null",
  "confidence": 0.0,
  "extracted_data": {{}},
  "fields_to_mark_tbd": [],
  "assistant_reply": "string"
}}

Additional guidance:
- If USER_MESSAGE is a skip/TBD type response and CURRENT_SESSION.last_requested_fields has values,
  put those fields into fields_to_mark_tbd.
- If a field is marked TBD, do not put it in missing fields.
- Do not invent field names. Use only field names from the selected schema.
"""

    try:
        response_content = await call_openai_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt_content,
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        if isinstance(response_content, dict):
            raw_result = response_content
        else:
            raw_result = json.loads(response_content)

        return normalize_analysis_result(
            raw_result=raw_result,
            session=session,
            user_message=user_message,
        )

    except json.JSONDecodeError:
        print("Error: OpenAI API returned invalid JSON.")

        fallback_result = {
            "intent": "skip_field" if looks_like_skip_request(user_message) else "unclear",
            "contract_type": session.get("detected_contract_type"),
            "confidence": 0.0,
            "extracted_data": {},
            "fields_to_mark_tbd": session.get("last_requested_fields", [])
            if looks_like_skip_request(user_message)
            else [],
            "assistant_reply": "I apologize, I encountered an issue processing your request. Could you please rephrase?",
        }

        return normalize_analysis_result(
            raw_result=fallback_result,
            session=session,
            user_message=user_message,
        )

    except Exception as e:
        print(f"Error in analyze_contract_chat_with_openai: {e}")

        fallback_result = {
            "intent": "skip_field" if looks_like_skip_request(user_message) else "unclear",
            "contract_type": session.get("detected_contract_type"),
            "confidence": 0.0,
            "extracted_data": {},
            "fields_to_mark_tbd": session.get("last_requested_fields", [])
            if looks_like_skip_request(user_message)
            else [],
            "assistant_reply": "I'm sorry, but I'm having trouble understanding right now. Please try again or rephrase your request.",
        }

        return normalize_analysis_result(
            raw_result=fallback_result,
            session=session,
            user_message=user_message,
        )


# ---------------------------------------------------------------------
# Contract type resolver
# ---------------------------------------------------------------------

def resolve_contract_type(analysis_result: dict, session: dict) -> str | None:
    """
    Validates and resolves contract type.

    Rule:
    - Keep the current session contract type unless the model is highly confident
      about a valid different type.
    This prevents accidental contract-type switching mid-conversation.
    """

    analysis_result = analysis_result or {}
    session = session or {}

    model_contract_type = analysis_result.get("contract_type")
    confidence = safe_float(analysis_result.get("confidence", 0.0), 0.0)

    valid_types = get_valid_contract_types()
    session_contract_type = session.get("detected_contract_type")

    if session_contract_type and session_contract_type in valid_types:
        # Same type with moderate confidence is okay.
        if model_contract_type == session_contract_type and confidence >= 0.4:
            return session_contract_type

        # Different type requires high confidence.
        if (
            model_contract_type
            and model_contract_type in valid_types
            and model_contract_type != session_contract_type
            and confidence >= 0.85
        ):
            return model_contract_type

        # Otherwise preserve existing session type.
        return session_contract_type

    # No session type yet.
    if model_contract_type and model_contract_type in valid_types and confidence >= 0.7:
        return model_contract_type

    return None


# ---------------------------------------------------------------------
# Extracted data filtering
# ---------------------------------------------------------------------

def filter_extracted_data(contract_type: str | None, extracted_data: dict) -> dict:
    """
    Filters extracted data based on selected contract schema.

    Important:
    - Empty values are removed.
    - TBD-like values are allowed because they represent intentional incomplete values.
    """

    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return {}

    if not isinstance(extracted_data, dict):
        return {}

    allowed_fields = get_schema_fields(contract_type)

    filtered = {}
    for key, value in extracted_data.items():
        if key not in allowed_fields:
            continue

        if is_empty_value(value):
            continue

        filtered[key] = value

    return filtered


# ---------------------------------------------------------------------
# Missing / incomplete field calculation
# ---------------------------------------------------------------------

def get_missing_fields_for_draft(
    contract_type: str | None,
    collected_data: dict,
    field_meta: dict = None
) -> list[str]:
    """
    Calculates truly missing required fields.

    Important anti-loop behavior:
    - "TBD" is NOT missing.
    - "unknown", "not sure", "leave blank", etc. are NOT missing if stored intentionally.
    - Empty/None/nonexistent fields ARE missing.

    This function should only return fields that have no value at all.
    Incomplete placeholder values should be handled by get_incomplete_fields_for_draft().
    """

    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return []

    collected_data = collected_data or {}
    required = get_required_fields(contract_type)

    missing = []

    for field in required:
        if field not in collected_data:
            missing.append(field)
            continue

        value = collected_data.get(field)

        # Empty is missing.
        if is_empty_value(value):
            missing.append(field)
            continue

        # TBD is intentionally present; it is incomplete, not missing.
        # So do NOT append it to missing.
        if is_tbd_value(value):
            continue

    return missing


def get_incomplete_fields_for_draft(
    contract_type: str | None,
    collected_data: dict,
    field_meta: dict = None
) -> list[str]:
    """
    Calculates required fields that are present but incomplete/placeholder.

    Example:
    - "TBD"
    - "unknown"
    - "not sure"
    - "[insert date]"

    These fields should not cause the bot to ask the same question repeatedly.
    They can be listed later for user confirmation before draft generation.
    """

    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return []

    collected_data = collected_data or {}
    required = get_required_fields(contract_type)

    incomplete = []

    for field in required:
        if field not in collected_data:
            continue

        value = collected_data.get(field)

        if is_empty_value(value):
            continue

        if is_tbd_value(value):
            incomplete.append(field)

    return incomplete


def mark_fields_as_tbd(
    contract_type: str | None,
    collected_data: dict,
    fields_to_mark_tbd: list[str],
) -> dict:
    """
    Applies TBD to valid schema fields.

    This helper is optional, but useful if the caller wants this analyzer to
    directly update collected_data after detecting skipped fields.
    """

    collected_data = dict(collected_data or {})

    valid_fields = filter_fields_for_schema(contract_type, fields_to_mark_tbd)

    for field in valid_fields:
        # Do not overwrite meaningful non-placeholder values.
        existing_value = collected_data.get(field)

        if is_empty_value(existing_value) or is_tbd_value(existing_value):
            collected_data[field] = TBD_VALUE

    return collected_data
