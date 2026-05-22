# app/services/contract_field_rules.py

from typing import Any, Dict, List, Optional, Tuple

from app.services.contract_registry import (
    FieldDefinition,
    get_all_fields,
    get_contract_definition,
    get_optional_fields,
    get_required_fields,
    is_supported_contract_type,
)


# ---------------------------------------------------------------------
# Basic value handling
# ---------------------------------------------------------------------

def is_empty_value(value: Any) -> bool:
    """
    Check whether a field value should be treated as empty.
    """
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0

    return False


def normalize_collected_fields(collected_fields: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize collected fields to prevent None errors.
    """
    if not collected_fields:
        return {}

    normalized = {}

    for key, value in collected_fields.items():
        if isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value

    return normalized


# ---------------------------------------------------------------------
# Required and optional field helpers
# ---------------------------------------------------------------------

def get_required_field_keys(contract_type: str) -> List[str]:
    """
    Return required field keys for a contract type.
    """
    return [field.key for field in get_required_fields(contract_type)]


def get_optional_field_keys(contract_type: str) -> List[str]:
    """
    Return optional field keys for a contract type.
    """
    return [field.key for field in get_optional_fields(contract_type)]


def get_all_field_keys(contract_type: str) -> List[str]:
    """
    Return all field keys for a contract type.
    """
    return [field.key for field in get_all_fields(contract_type)]


def get_field_definition(contract_type: str, field_key: str) -> Optional[FieldDefinition]:
    """
    Return a field definition by key for a given contract type.
    """
    for field in get_all_fields(contract_type):
        if field.key == field_key:
            return field
    return None


def get_missing_required_fields(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> List[FieldDefinition]:
    """
    Return required fields that are not yet collected.
    """
    collected_fields = normalize_collected_fields(collected_fields)

    missing = []
    for field in get_required_fields(contract_type):
        if is_empty_value(collected_fields.get(field.key)):
            missing.append(field)

    return missing


def get_missing_optional_fields(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> List[FieldDefinition]:
    """
    Return optional fields that are not yet collected.
    """
    collected_fields = normalize_collected_fields(collected_fields)

    missing = []
    for field in get_optional_fields(contract_type):
        if is_empty_value(collected_fields.get(field.key)):
            missing.append(field)

    return missing


def get_missing_fields(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
    include_optional: bool = False,
) -> List[FieldDefinition]:
    """
    Return missing required fields, and optionally missing optional fields.
    """
    missing = get_missing_required_fields(contract_type, collected_fields)

    if include_optional:
        missing.extend(get_missing_optional_fields(contract_type, collected_fields))

    return missing


def has_all_required_fields(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> bool:
    """
    Check whether all required fields are collected.
    """
    return len(get_missing_required_fields(contract_type, collected_fields)) == 0


def is_ready_for_drafting(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> bool:
    """
    Check whether contract has enough data to generate a draft.
    """
    if not is_supported_contract_type(contract_type):
        return False

    return has_all_required_fields(contract_type, collected_fields)


# ---------------------------------------------------------------------
# Follow-up question generation
# ---------------------------------------------------------------------

def format_example_text(field: FieldDefinition) -> str:
    """
    Format example text for a field.
    """
    if field.example:
        return f" For example: {field.example}."
    return ""


def build_field_question(field: FieldDefinition) -> str:
    """
    Build a user-friendly question for a single field.
    """
    question = field.question.strip()

    if not question.endswith("?"):
        question += "?"

    example_text = format_example_text(field)

    return f"{question}{example_text}"


def get_next_required_question(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Return the next required follow-up question.
    """
    missing = get_missing_required_fields(contract_type, collected_fields)

    if not missing:
        return None

    return build_field_question(missing[0])


def get_next_optional_question(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Return the next optional follow-up question.
    """
    missing = get_missing_optional_fields(contract_type, collected_fields)

    if not missing:
        return None

    return build_field_question(missing[0])


def get_next_question(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
    ask_optional: bool = False,
) -> Optional[str]:
    """
    Return next follow-up question.

    Priority:
    1. Required fields
    2. Optional fields, only if ask_optional=True
    """
    required_question = get_next_required_question(contract_type, collected_fields)
    if required_question:
        return required_question

    if ask_optional:
        return get_next_optional_question(contract_type, collected_fields)

    return None


def get_missing_fields_summary(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
    include_optional: bool = False,
) -> Dict[str, Any]:
    """
    Return a structured summary of missing fields.
    Useful for API responses.
    """
    required_missing = get_missing_required_fields(contract_type, collected_fields)
    optional_missing = get_missing_optional_fields(contract_type, collected_fields)

    result = {
        "contract_type": contract_type,
        "required_missing_count": len(required_missing),
        "optional_missing_count": len(optional_missing),
        "required_missing": [
            {
                "key": field.key,
                "label": field.label,
                "question": build_field_question(field),
                "example": field.example,
                "field_type": field.field_type,
            }
            for field in required_missing
        ],
        "optional_missing": [],
        "ready_for_drafting": len(required_missing) == 0,
        "next_question": get_next_question(
            contract_type,
            collected_fields,
            ask_optional=include_optional,
        ),
    }

    if include_optional:
        result["optional_missing"] = [
            {
                "key": field.key,
                "label": field.label,
                "question": build_field_question(field),
                "example": field.example,
                "field_type": field.field_type,
            }
            for field in optional_missing
        ]

    return result


# ---------------------------------------------------------------------
# Conversation-oriented helpers
# ---------------------------------------------------------------------

def build_contract_intro_message(contract_type: str) -> str:
    """
    Build an intro message after contract type has been detected.
    """
    definition = get_contract_definition(contract_type)

    if not definition:
        return (
            "I can help draft your agreement, but I need to know which type of "
            "contract you want to create."
        )

    return (
        f"Great. I can help draft a {definition.title}. "
        f"I'll ask a few questions to collect the required details."
    )


def build_ready_to_draft_message(contract_type: str) -> str:
    """
    Build message when all required fields have been collected.
    """
    definition = get_contract_definition(contract_type)
    title = definition.title if definition else "agreement"

    return (
        f"Thanks. I now have the required information to draft the {title}. "
        f"I can generate the draft now."
    )


def build_optional_fields_offer(contract_type: str) -> Optional[str]:
    """
    Ask user whether they want to provide optional fields.
    """
    optional_fields = get_optional_fields(contract_type)

    if not optional_fields:
        return None

    labels = ", ".join([field.label for field in optional_fields[:3]])

    if len(optional_fields) > 3:
        labels += ", and other optional details"

    return (
        f"I have the required details. Would you like to add optional details "
        f"such as {labels}, or should I draft the agreement now?"
    )


def build_missing_fields_message(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> str:
    """
    Build a conversational message for the next missing required field.
    """
    definition = get_contract_definition(contract_type)

    if not definition:
        return "Which type of contract would you like to create?"

    next_question = get_next_required_question(contract_type, collected_fields)

    if next_question:
        return next_question

    return build_ready_to_draft_message(contract_type)


def get_conversation_status(
    contract_type: Optional[str],
    collected_fields: Optional[Dict[str, Any]],
    ask_optional: bool = False,
) -> Dict[str, Any]:
    """
    Return the current conversation status for contract drafting.
    """
    collected_fields = normalize_collected_fields(collected_fields)

    if not contract_type:
        return {
            "status": "missing_contract_type",
            "contract_type": None,
            "ready_for_drafting": False,
            "message": "What type of contract would you like to create?",
            "next_question": "What type of contract would you like to create?",
            "missing_required_fields": [],
            "missing_optional_fields": [],
        }

    if not is_supported_contract_type(contract_type):
        return {
            "status": "unsupported_contract_type",
            "contract_type": contract_type,
            "ready_for_drafting": False,
            "message": (
                "That contract type is not currently supported. "
                "Please choose another contract type."
            ),
            "next_question": "What type of contract would you like to create?",
            "missing_required_fields": [],
            "missing_optional_fields": [],
        }

    required_missing = get_missing_required_fields(contract_type, collected_fields)
    optional_missing = get_missing_optional_fields(contract_type, collected_fields)

    if required_missing:
        next_question = build_field_question(required_missing[0])
        return {
            "status": "collecting_required_fields",
            "contract_type": contract_type,
            "ready_for_drafting": False,
            "message": next_question,
            "next_question": next_question,
            "missing_required_fields": [field.key for field in required_missing],
            "missing_optional_fields": [field.key for field in optional_missing],
        }

    if ask_optional and optional_missing:
        next_question = build_field_question(optional_missing[0])
        return {
            "status": "collecting_optional_fields",
            "contract_type": contract_type,
            "ready_for_drafting": False,
            "message": next_question,
            "next_question": next_question,
            "missing_required_fields": [],
            "missing_optional_fields": [field.key for field in optional_missing],
        }

    return {
        "status": "ready_for_drafting",
        "contract_type": contract_type,
        "ready_for_drafting": True,
        "message": build_ready_to_draft_message(contract_type),
        "next_question": None,
        "missing_required_fields": [],
        "missing_optional_fields": [field.key for field in optional_missing],
    }


# ---------------------------------------------------------------------
# Field merge helpers
# ---------------------------------------------------------------------

def merge_collected_fields(
    current_fields: Optional[Dict[str, Any]],
    new_fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merge newly extracted fields into current collected fields.

    Empty new values do not overwrite existing values.
    """
    current_fields = normalize_collected_fields(current_fields)
    new_fields = normalize_collected_fields(new_fields)

    merged = dict(current_fields)

    for key, value in new_fields.items():
        if not is_empty_value(value):
            merged[key] = value

    return merged


def filter_fields_for_contract_type(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
    keep_unknown: bool = False,
) -> Dict[str, Any]:
    """
    Keep only fields known for the selected contract type.

    If keep_unknown=True, it returns all fields unchanged.
    """
    fields = normalize_collected_fields(fields)

    if keep_unknown:
        return fields

    allowed_keys = set(get_all_field_keys(contract_type))

    return {
        key: value
        for key, value in fields.items()
        if key in allowed_keys
    }


def prepare_fields_for_contract(
    contract_type: str,
    current_fields: Optional[Dict[str, Any]],
    new_fields: Optional[Dict[str, Any]],
    keep_unknown: bool = False,
) -> Dict[str, Any]:
    """
    Merge and filter fields for a contract type.
    """
    merged = merge_collected_fields(current_fields, new_fields)
    return filter_fields_for_contract_type(
        contract_type=contract_type,
        fields=merged,
        keep_unknown=keep_unknown,
    )


# ---------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------
# These aliases help if your existing code already imports older function names.

def required_fields_for(contract_type: str) -> List[str]:
    """
    Backward-compatible alias.
    """
    return get_required_field_keys(contract_type)


def optional_fields_for(contract_type: str) -> List[str]:
    """
    Backward-compatible alias.
    """
    return get_optional_field_keys(contract_type)


def missing_fields_for(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Backward-compatible alias returning only missing required field keys.
    """
    return [
        field.key
        for field in get_missing_required_fields(contract_type, collected_fields)
    ]


def next_question_for(
    contract_type: str,
    collected_fields: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Backward-compatible alias.
    """
    return get_next_required_question(contract_type, collected_fields)
