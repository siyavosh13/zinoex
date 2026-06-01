import os
import json
import re
from typing import Dict, Optional, List, Any
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=300.0)


DEFAULT_FALLBACK_CONTRACT_TYPE = "general_contract"


def get_valid_contract_types(contract_schemas: Dict[str, Any]) -> List[str]:
    """
    Return valid contract type keys dynamically from CONTRACT_SCHEMAS.
    This makes the chatbot automatically adapt when contract types are added or removed.
    """
    if not contract_schemas or not isinstance(contract_schemas, dict):
        return []
    return list(contract_schemas.keys())


def get_fallback_contract_type(contract_schemas: Dict[str, Any]) -> Optional[str]:
    """
    Return the fallback contract type if available.
    By default, the system uses general_contract for unknown or unsupported contract requests.
    """
    valid_contract_types = get_valid_contract_types(contract_schemas)

    if DEFAULT_FALLBACK_CONTRACT_TYPE in valid_contract_types:
        return DEFAULT_FALLBACK_CONTRACT_TYPE

    return None


def is_contract_related_intent(intent: str) -> bool:
    """
    Determines whether an intent is related to creating or continuing a contract intake flow.
    This prevents unrelated/general questions from being forced into general_contract.
    """
    return intent in [
        "start_contract",
        "provide_info",
        "request_draft",
        "confirm_generate",
        "fill_missing",
        "skip_field",
    ]


def resolve_contract_type_with_fallback(
    detected_type: Optional[str],
    current_type: Optional[str],
    contract_schemas: Dict[str, Any],
    intent: str = "unclear",
) -> Optional[str]:
    """
    Safely resolve the contract type.

    Priority:
    1. If detected_type is valid, use it.
    2. If current_type is already valid, keep it.
    3. If the user is doing a contract-related action but detected_type is missing/invalid,
       fall back to general_contract if it exists.
    4. Otherwise return None.
    """
    valid_contract_types = set(get_valid_contract_types(contract_schemas))
    fallback_contract_type = get_fallback_contract_type(contract_schemas)

    if detected_type in valid_contract_types:
        return detected_type

    if current_type in valid_contract_types:
        return current_type

    if is_contract_related_intent(intent) and fallback_contract_type:
        return fallback_contract_type

    return None


def extract_json(text: str):
    """
    Extract and sanitize JSON from model output.
    If parsing fails, return a safe fallback payload.
    """

    if not text:
        return {
            "overall_score": 0,
            "summary": "Empty response",
            "risks": [],
            "suggestions": []
        }

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {
            "overall_score": 0,
            "summary": "No JSON detected",
            "risks": [],
            "suggestions": [],
            "raw_output": text
        }

    json_str = match.group(0)

    json_str = (
        json_str
        .replace("\n", "")
        .replace("\t", "")
        .replace("’", "'")
    )

    if re.search(r"'[a-zA-Z0-9_ ]+':", json_str):
        json_str = json_str.replace("'", "\"")

    try:
        return json.loads(json_str)
    except Exception as e:
        return {
            "overall_score": 0,
            "summary": f"JSON parsing failed: {str(e)}",
            "risks": [],
            "suggestions": [],
            "raw_output": json_str
        }


def normalize_contract_length(value: str) -> str:
    if not value:
        return "medium"

    value = str(value).strip().lower()

    if value in ["short"]:
        return "short"

    if value in ["medium", "normal", "standard"]:
        return "medium"

    if value in ["long", "detailed", "full"]:
        return "long"

    return "medium"


def get_contract_length(answers: Dict) -> str:
    if not answers:
        return "medium"

    possible_keys = [
        "contract_length",
        "Contract length",
        "contract length",
        "How detailed should the generated contract be?",
        "how detailed should the generated contract be?"
    ]

    for key in possible_keys:
        if key in answers and answers.get(key):
            return normalize_contract_length(answers.get(key))

    for key, value in answers.items():
        key_text = str(key).strip().lower()
        if "how detailed" in key_text and "contract" in key_text:
            return normalize_contract_length(value)

    return "medium"


def get_contract_length_instruction(contract_length: str) -> str:
    contract_length = normalize_contract_length(contract_length)

    if contract_length == "short":
        return """
Length requirement:
Generate a SHORT contract.
Keep it concise, practical, and easy to read.
Include only the essential legal sections needed for this type of agreement.
Avoid unnecessary repetition, overly long definitions, and excessive legal boilerplate.
The contract should still be complete and usable, but compact.
"""

    if contract_length == "long":
        return """
Length requirement:
Generate a LONG and highly detailed contract.
The contract must be comprehensive, formal, and professionally structured.

Include detailed clauses where relevant, such as:
- Title and introductory paragraph
- Identification of the parties
- Background / recitals if appropriate
- Definitions if useful
- Scope, duties, responsibilities, or services
- Payment, compensation, fees, taxes, and expenses where applicable
- Term, renewal, suspension, and termination
- Confidentiality
- Intellectual property ownership and licenses where applicable
- Data protection, privacy, or security obligations where applicable
- Representations and warranties
- Disclaimers
- Limitation of liability
- Indemnification
- Non-solicitation or non-compete if applicable and requested
- Compliance with laws
- Dispute resolution
- Governing law and jurisdiction
- Notices
- Assignment
- Force majeure
- Severability
- Waiver
- Entire agreement
- Amendments
- Counterparts / electronic signatures if appropriate
- Signature blocks

Use clear section headings and numbered clauses.
Expand each important clause with practical legal detail.
If the user did not provide certain information, use clear placeholders such as [Insert Name], [Insert Date], or [Insert Jurisdiction].
Do not invent sensitive facts that the user did not provide.
"""

    return """
Length requirement:
Generate a MEDIUM-length contract.
The contract should be balanced: more complete than a short template, but not overly lengthy.
Include the standard important sections for this contract type with clear headings and practical legal wording.
Avoid excessive boilerplate, but make sure the agreement is complete, coherent, and ready for review.
If information is missing, use clear placeholders such as [Insert Name], [Insert Date], or [Insert Jurisdiction].
"""


def get_max_output_tokens_by_length(contract_length: str) -> int:
    contract_length = normalize_contract_length(contract_length)

    if contract_length == "short":
        return 2500

    if contract_length == "long":
        return 8000

    return 4500


async def generate_contract_with_model(
    contract_type: str,
    language: str,
    tone: str,
    context: str,
    answers: Dict,
) -> str:

    contract_length = get_contract_length(answers)
    length_instruction = get_contract_length_instruction(contract_length)
    max_output_tokens = get_max_output_tokens_by_length(contract_length)

    system_prompt = (
        "You are a legal contract drafting assistant. "
        "You must generate clear, legally coherent, complete, and well-structured contracts. "
        "Follow the requested contract length carefully. "
        "Default to common-law drafting style suitable for Canada unless the provided user data clearly indicates a different jurisdiction."
    )

    user_prompt = f"""
Contract type: {contract_type}
Language: {language}
Tone: {tone}
Selected contract length: {contract_length}

Context:
{context or "-"}

Answers:
{answers or {}}

{length_instruction}

Drafting instructions:
- Return a full contract in the requested language.
- Use the user's answers as the main source of contract details.
- Draft in a professional style suitable for Canada unless the user specifies another jurisdiction.
- Do not ignore the selected contract length.
- If important information is missing, use clear placeholders instead of inventing facts.
- Use professional legal formatting with clear headings.
"""

    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_output_tokens=max_output_tokens,
    )

    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    return response.output[0].content[0].text


async def review_contract_with_model(text: str, language: str = "en"):
    contract_text = text[:50000]

    try:
        messages = [
            {"role": "system", "content": "You are an AI contract analyzer. Return ONLY pure JSON."},
            {
                "role": "user",
                "content": (
                    f"Language: {language}\n\n"
                    f"Contract:\n{contract_text}\n\n"
                    "Return JSON keys: overall_score, summary, risks, suggestions."
                ),
            }
        ]

        response = await client.responses.create(
            model="gpt-4o-mini",
            input=messages,
            max_output_tokens=4000,
            timeout=300
        )

        if hasattr(response, "output_text") and response.output_text:
            ai_text = response.output_text
        else:
            ai_text = response.output[0].content[0].text

        ai_text = ai_text.strip()
        data = extract_json(ai_text)
        return data

    except Exception as e:
        return {
            "overall_score": 0,
            "summary": f"Error: {str(e)}",
            "risks": [],
            "suggestions": []
        }


def sanitize_chat_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except Exception:
        try:
            json_str = json_str.replace("\n", " ").replace("\t", " ").replace("’", "'")
            return json.loads(json_str)
        except Exception:
            return {}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_empty_value(value: Any) -> bool:
    """
    True only when the field is genuinely empty and should still be asked.

    Important:
    - "TBD" is NOT empty here.
    - "unknown", "not sure", "skip", etc. are also not empty here if they are stored intentionally.
    - This function is used for normal intake flow, so skipped/TBD fields are not asked again.
    """
    if value is None:
        return True

    value = normalize_text(value)
    if not value:
        return True

    return False


def is_tbd_value(value: Any) -> bool:
    """
    True when the user intentionally chose to leave the field as TBD / skipped.
    These values should NOT be asked again during normal intake.
    """
    if value is None:
        return False

    text = normalize_text(value).lower()

    tbd_values = {
        "tbd",
        "[tbd]",
        "to be determined",
        "to be decided",
        "decide later",
        "later",
        "skip",
        "skipped",
        "unknown",
        "not sure",
        "n/a",
        "na",
    }

    return text in tbd_values


def is_placeholder_value(value: Any) -> bool:
    """
    Used for final draft placeholder replacement.

    In draft generation, TBD-like values should be converted into readable placeholders
    such as [TBD: effective date].
    """
    if is_empty_value(value):
        return True

    text = normalize_text(value).lower()

    if is_tbd_value(value):
        return True

    placeholders = {
        "[insert]",
        "placeholder",
    }

    return text in placeholders


def looks_like_skip_request(user_message: str) -> bool:
    """
    Rule-based skip detector.

    This prevents the system from relying only on the model to return fields_to_mark_tbd.
    If the user says "skip", "TBD", "later", etc., we mark the last requested field(s)
    as TBD.
    """
    text = normalize_text(user_message).lower()
    if not text:
        return False

    skip_phrases = {
        "skip",
        "skip it",
        "skip this",
        "leave it",
        "leave it blank",
        "leave blank",
        "tbd",
        "mark as tbd",
        "put tbd",
        "use tbd",
        "unknown",
        "not sure",
        "i don't know",
        "i dont know",
        "decide later",
        "later",
        "n/a",
        "na",
        "رد کن",
        "ردش کن",
        "بعدا",
        "بعداً",
        "بعدا میگم",
        "بعداً میگم",
        "نمیدونم",
        "نمی دونم",
        "فعلا نه",
        "فعلاً نه",
        "خالی بذار",
        "خالی بزار",
        "معلوم نیست",
    }

    if text in skip_phrases:
        return True

    return any(phrase in text for phrase in skip_phrases)


def get_schema_fields(contract_schema: Dict[str, Any]) -> List[str]:
    if not contract_schema:
        return []
    return list(contract_schema.get("required_fields", [])) + list(contract_schema.get("optional_fields", []))


def get_missing_required_fields(contract_schema: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
    """
    Missing fields for the normal question-asking flow.

    Important:
    - This function should only return genuinely empty fields.
    - Fields intentionally marked as TBD should NOT be returned here.
    - This prevents the chatbot from asking the same skipped field again and again.
    """
    if not contract_schema:
        return []

    missing = []
    for field in contract_schema.get("required_fields", []):
        value = collected_data.get(field)
        if is_empty_value(value):
            missing.append(field)

    return missing


def get_incomplete_required_fields_for_finalization(
    contract_schema: Dict[str, Any],
    collected_data: Dict[str, Any],
) -> List[str]:
    """
    Incomplete fields for finalization warning.

    This function includes both:
    - genuinely empty fields
    - fields intentionally marked as TBD

    It is useful when the user requests a draft and you want to warn them that
    the final contract will contain TBD placeholders.
    """
    if not contract_schema:
        return []

    incomplete = []
    for field in contract_schema.get("required_fields", []):
        value = collected_data.get(field)

        if is_empty_value(value) or is_tbd_value(value):
            incomplete.append(field)

    return incomplete


def merge_extracted_data(
    existing: Dict[str, Any],
    new_data: Dict[str, Any],
    allowed_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    result = dict(existing or {})
    new_data = new_data or {}

    for key, value in new_data.items():
        if allowed_fields and key not in allowed_fields:
            continue
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        result[key] = value

    return result


def detect_user_confirmed_generate_intent(user_message: str) -> bool:
    text = normalize_text(user_message).lower()
    if not text:
        return False

    phrases = [
        "generate it",
        "generate the draft",
        "generate draft",
        "create the draft",
        "draft it",
        "proceed",
        "go ahead",
        "yes generate",
        "yes, generate",
        "yes generate it",
        "yes, generate it",
        "continue and generate",
        "use tbd",
        "leave it as tbd",
        "that's fine, generate it",
        "that is fine, generate it",
        "okay generate it",
        "ok generate it",
        "yes proceed",
        "proceed with the draft",
    ]
    return any(p in text for p in phrases)


def detect_fill_missing_instead_intent(user_message: str) -> bool:
    text = normalize_text(user_message).lower()
    if not text:
        return False

    phrases = [
        "i will provide it",
        "i'll provide it",
        "let me provide it",
        "i want to fill it",
        "i want to complete it",
        "ask me",
        "ask the next question",
        "let's continue",
        "lets continue",
        "continue collecting",
        "i will answer",
        "i'll answer",
        "i want to answer",
        "don't generate yet",
        "do not generate yet",
        "not yet",
        "wait",
        "i want to add more",
        "i want to provide more details",
        "i will give the missing details",
        "i'll give the missing details",
        "i can provide that",
        "i can answer that",
        "sure, ask me",
        "okay, ask me",
        "ok, ask me",
        "okay i will provide it",
        "ok i will provide it",
        "باشه میگم",
        "میگم",
        "الان میگم",
        "بگم",
        "میخوام کاملش کنم",
        "نخیر اول کاملش میکنم",
        "فعلا تولید نکن",
        "فعلاً تولید نکن",
        "هنوز نه",
        "ادامه بده",
    ]
    return any(p in text for p in phrases)


def get_finalization_missing_fields(contract_schema: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
    """
    Fields that are incomplete for finalization warning.

    Unlike get_missing_required_fields(), this includes TBD fields.
    """
    return get_incomplete_required_fields_for_finalization(contract_schema, collected_data)


async def analyze_contract_chat_with_model(
    user_message: str,
    session: Dict[str, Any],
    contract_schemas: Dict[str, Any],
) -> Dict[str, Any]:
    current_session_view = {
        "detected_contract_type": session.get("detected_contract_type"),
        "collected_data": session.get("collected_data", {}),
        "last_requested_fields": session.get("last_requested_fields", []),
        "status": session.get("status"),
        "pending_draft_confirmation": session.get("pending_draft_confirmation", False),
        "pending_finalization_missing_fields": session.get("pending_finalization_missing_fields", []),
        "last_missing_prompt": session.get("last_missing_prompt"),

        # Newer router/session keys. Including them here gives the model fuller context.
        "awaiting_incomplete_fields_confirmation": session.get("awaiting_incomplete_fields_confirmation", False),
        "pending_incomplete_fields": session.get("pending_incomplete_fields", []),
        "allow_generation_with_incomplete": session.get("allow_generation_with_incomplete", False),
    }

    valid_contract_types = get_valid_contract_types(contract_schemas)
    fallback_contract_type = get_fallback_contract_type(contract_schemas)

    system_prompt = f"""
You are an AI assistant for a contract-generation chatbot.

Your job:
- Understand the user's goal.
- Detect the most appropriate contract type from the provided CONTRACT_SCHEMAS.
- Extract any structured data the user provides for contract fields.
- Decide whether the user is answering a previous question, starting a new contract, asking for the draft, confirming generation, asking a general question, asking to skip a field, or choosing to fill missing fields first.

Dynamic contract type rules:
- You must choose contract_type ONLY from the provided CONTRACT_SCHEMAS keys.
- The valid contract types are:
{json.dumps(valid_contract_types, ensure_ascii=False)}
- Do not invent contract types outside the schema.
- If the user clearly wants a contract but the exact type is not available in CONTRACT_SCHEMAS, set contract_type to "{fallback_contract_type}".
- If the requested contract type is unusual, unsupported, custom, or not clearly matched to any schema key, use "{fallback_contract_type}" as the safe fallback.
- Only set contract_type to null when the user's message is not clearly asking to start, continue, or generate a contract and no current contract context applies.
- If using "{fallback_contract_type}" because there is no exact schema match, assistant_reply should briefly explain that you can help using a general contract format and continue collecting information.

Rules:
- Return ONLY valid JSON.
- Do not invent contract types outside the schema.
- Keep assistant_reply concise and helpful.
- If contract type is unclear and the user is not clearly asking for a contract, set contract_type to null.
- fields_to_mark_tbd should include fields the user wants to skip, leave blank, or decide later.
- If the user says skip, TBD, unknown, not sure, later, leave blank, or similar, use intent: "skip_field".
- If the user says skip/TBD without naming a field, use CURRENT_SESSION.last_requested_fields to infer the field(s).
- extracted_data should only include data actually provided by the user.
- If the user is responding to a pending draft confirmation and wants to provide the missing details first, use intent: "fill_missing".
"""

    user_prompt = f"""
CONTRACT_SCHEMAS:
{json.dumps(contract_schemas, ensure_ascii=False, indent=2)}

CURRENT_SESSION:
{json.dumps(current_session_view, ensure_ascii=False, indent=2)}

USER_MESSAGE:
{user_message}

Return JSON in exactly this structure:
{{
  "intent": "start_contract | provide_info | ask_question | request_draft | confirm_generate | fill_missing | skip_field | unclear",
  "contract_type": null,
  "confidence": 0.0,
  "extracted_data": {{}},
  "fields_to_mark_tbd": [],
  "assistant_reply": ""
}}
"""

    try:
        response = await client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_output_tokens=2500,
        )

        if hasattr(response, "output_text") and response.output_text:
            ai_text = response.output_text
        else:
            ai_text = response.output[0].content[0].text

        parsed = sanitize_chat_json(ai_text)

        if not parsed:
            return {
                "intent": "unclear",
                "contract_type": None,
                "confidence": 0.0,
                "extracted_data": {},
                "fields_to_mark_tbd": [],
                "assistant_reply": "Could you please clarify what kind of contract you need?"
            }

        parsed_intent = parsed.get("intent", "unclear")
        parsed_contract_type = parsed.get("contract_type")

        resolved_contract_type = resolve_contract_type_with_fallback(
            detected_type=parsed_contract_type,
            current_type=session.get("detected_contract_type"),
            contract_schemas=contract_schemas,
            intent=parsed_intent,
        )

        assistant_reply = parsed.get("assistant_reply", "") or ""

        if (
            parsed_contract_type
            and parsed_contract_type not in valid_contract_types
            and resolved_contract_type == fallback_contract_type
            and is_contract_related_intent(parsed_intent)
            and not assistant_reply
        ):
            assistant_reply = (
                "I do not have a dedicated template for that exact contract type, "
                "but I can help you draft it using a general contract format."
            )

        if (
            not parsed_contract_type
            and resolved_contract_type == fallback_contract_type
            and is_contract_related_intent(parsed_intent)
            and not assistant_reply
        ):
            assistant_reply = (
                "I can help you draft this using a general contract format. "
                "Let’s collect the key details."
            )

        fields_to_mark_tbd = parsed.get("fields_to_mark_tbd", []) or []
        if not isinstance(fields_to_mark_tbd, list):
            fields_to_mark_tbd = []

        return {
            "intent": parsed_intent,
            "contract_type": resolved_contract_type,
            "confidence": parsed.get("confidence", 0.0),
            "extracted_data": parsed.get("extracted_data", {}) or {},
            "fields_to_mark_tbd": fields_to_mark_tbd,
            "assistant_reply": assistant_reply,
        }

    except Exception:
        return {
            "intent": "unclear",
            "contract_type": None,
            "confidence": 0.0,
            "extracted_data": {},
            "fields_to_mark_tbd": [],
            "assistant_reply": "I’m sorry, I had trouble understanding your message. Could you please rephrase it?"
        }


async def generate_next_chat_question_with_model(
    contract_type: str,
    contract_schema: Dict[str, Any],
    next_field: str,
    collected_data: Dict[str, Any],
    language: str = "en",
) -> str:
    system_prompt = """
You are an AI contract assistant.
Ask only ONE clear and concise question.
Do not ask multiple questions at once.
Do not provide legal advice.
Use natural, professional, user-friendly wording suitable for a contract intake chatbot for the Canadian market.
"""

    user_prompt = f"""
Language: {language}
Contract type: {contract_type}

Contract schema:
{json.dumps(contract_schema, ensure_ascii=False, indent=2)}

Collected data so far:
{json.dumps(collected_data, ensure_ascii=False, indent=2)}

Next field to collect:
{next_field}

Write one short, friendly, professional question asking the user for that field only.
Return only the question text.
"""

    try:
        response = await client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_output_tokens=300,
        )

        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        return response.output[0].content[0].text.strip()

    except Exception:
        readable = next_field.replace("_", " ").strip()
        return f"Could you please provide the {readable}?"


async def generate_contract_draft_from_chat_with_model(
    contract_type: str,
    language: str,
    tone: str,
    context: str,
    answers: Dict[str, Any],
    contract_schema: Optional[Dict[str, Any]] = None,
) -> str:
    final_answers = dict(answers or {})
    contract_schema = contract_schema or {}

    all_fields = get_schema_fields(contract_schema)
    for field in all_fields:
        if field not in final_answers or is_placeholder_value(final_answers.get(field)):
            final_answers[field] = f"[TBD: {field.replace('_', ' ')}]"

    return await generate_contract_with_model(
        contract_type=contract_type,
        language=language,
        tone=tone,
        context=context,
        answers=final_answers,
    )


async def run_contract_chatbot_turn(
    user_message: str,
    session: Dict[str, Any],
    contract_schemas: Dict[str, Any],
    language: str = "en",
    tone: str = "professional",
    context: str = "",
) -> Dict[str, Any]:
    if session is None:
        session = {}

    if "collected_data" not in session or not isinstance(session.get("collected_data"), dict):
        session["collected_data"] = {}

    if "last_requested_fields" not in session or not isinstance(session.get("last_requested_fields"), list):
        session["last_requested_fields"] = []

    if "status" not in session:
        session["status"] = "initializing"

    if "pending_draft_confirmation" not in session:
        session["pending_draft_confirmation"] = False

    if "pending_finalization_missing_fields" not in session or not isinstance(session.get("pending_finalization_missing_fields"), list):
        session["pending_finalization_missing_fields"] = []

    if "last_missing_prompt" not in session:
        session["last_missing_prompt"] = None

    # Defensive support for newer router/session keys.
    if "awaiting_incomplete_fields_confirmation" not in session:
        session["awaiting_incomplete_fields_confirmation"] = False

    if "pending_incomplete_fields" not in session or not isinstance(session.get("pending_incomplete_fields"), list):
        session["pending_incomplete_fields"] = []

    if "allow_generation_with_incomplete" not in session:
        session["allow_generation_with_incomplete"] = False

    analysis = await analyze_contract_chat_with_model(
        user_message=user_message,
        session=session,
        contract_schemas=contract_schemas,
    )

    valid_contract_types = set(get_valid_contract_types(contract_schemas))
    fallback_contract_type = get_fallback_contract_type(contract_schemas)

    detected_type = analysis.get("contract_type")
    current_type = session.get("detected_contract_type")
    user_intent = analysis.get("intent", "unclear")

    # Rule-based skip intent fallback.
    # This protects the flow even if the model fails to classify the message as skip_field.
    user_requested_skip = looks_like_skip_request(user_message)
    if user_requested_skip and user_intent not in ["confirm_generate", "request_draft"]:
        user_intent = "skip_field"

    resolved_type = resolve_contract_type_with_fallback(
        detected_type=detected_type,
        current_type=current_type,
        contract_schemas=contract_schemas,
        intent=user_intent,
    )

    if resolved_type in valid_contract_types:
        current_type = resolved_type
        session["detected_contract_type"] = resolved_type

    contract_schema = contract_schemas.get(current_type) if current_type in contract_schemas else None
    allowed_fields = get_schema_fields(contract_schema) if contract_schema else None

    extracted_data = analysis.get("extracted_data", {}) or {}
    merged_data = merge_extracted_data(
        existing=session.get("collected_data", {}),
        new_data=extracted_data,
        allowed_fields=allowed_fields,
    )

    fields_to_mark_tbd = analysis.get("fields_to_mark_tbd", []) or []
    if not isinstance(fields_to_mark_tbd, list):
        fields_to_mark_tbd = []

    # Rule-based fallback:
    # If the user says "skip", "TBD", "later", etc.,
    # mark the last requested field(s) as TBD even if the model forgot to return them.
    if user_requested_skip:
        last_requested = session.get("last_requested_fields", []) or []
        for field in last_requested:
            if field not in fields_to_mark_tbd:
                fields_to_mark_tbd.append(field)

    clean_tbd_fields = []
    for field in fields_to_mark_tbd:
        if not field:
            continue

        field = str(field).strip()

        if allowed_fields and field in allowed_fields:
            merged_data[field] = "TBD"
            clean_tbd_fields.append(field)

    # If the user skipped the currently requested field, remove it from last_requested_fields.
    if clean_tbd_fields:
        session["last_requested_fields"] = [
            field for field in session.get("last_requested_fields", [])
            if field not in clean_tbd_fields
        ]

    if "contract_type" in merged_data:
        merged_data.pop("contract_type", None)

    session["collected_data"] = merged_data

    if not current_type or not contract_schema:
        session["status"] = "awaiting_contract_type"
        return {
            "reply": analysis.get("assistant_reply") or "What type of contract would you like me to help you draft?",
            "draft": None,
            "session": session,
            "detected_contract_type": None,
            "missing_fields": [],
            "status": session["status"],
        }

    if current_type == fallback_contract_type and session.get("status") == "initializing":
        session["used_fallback_contract_type"] = True

    # missing_fields: fields that should still be asked in normal intake.
    # TBD fields are NOT included here.
    missing_fields = get_missing_required_fields(contract_schema, session["collected_data"])

    # finalization_missing_fields: fields that are incomplete for final warning.
    # This includes TBD fields.
    finalization_missing_fields = get_finalization_missing_fields(contract_schema, session["collected_data"])

    if user_intent == "confirm_generate" or detect_user_confirmed_generate_intent(user_message):
        user_confirmed_generate = True
    else:
        user_confirmed_generate = False

    if user_intent == "fill_missing" or detect_fill_missing_instead_intent(user_message):
        user_wants_to_fill_instead = True
    else:
        user_wants_to_fill_instead = False

    ready_to_draft = (
        bool(current_type)
        and bool(session.get("collected_data"))
        and not missing_fields
    )

    ready_to_finalize = (
        bool(current_type)
        and bool(session.get("collected_data"))
        and not finalization_missing_fields
    )

    if session.get("pending_draft_confirmation"):
        pending_fields = session.get("pending_finalization_missing_fields", []) or finalization_missing_fields

        # Only these are askable. Fields marked TBD should not be asked again.
        askable_pending_fields = [
            field for field in pending_fields
            if field in get_missing_required_fields(contract_schema, session["collected_data"])
        ]

        if user_wants_to_fill_instead:
            session["pending_draft_confirmation"] = False
            session["pending_finalization_missing_fields"] = askable_pending_fields

            if askable_pending_fields:
                next_field = askable_pending_fields[0]
                session["last_requested_fields"] = [next_field]

                next_question = await generate_next_chat_question_with_model(
                    contract_type=current_type,
                    contract_schema=contract_schema,
                    next_field=next_field,
                    collected_data=session["collected_data"],
                    language=language,
                )

                session["status"] = "collecting_info"
                session["last_missing_prompt"] = next_question

                return {
                    "reply": next_question,
                    "draft": None,
                    "session": session,
                    "detected_contract_type": current_type,
                    "missing_fields": askable_pending_fields,
                    "status": session["status"],
                }

            # If the only incomplete fields are TBD, do not ask them again.
            # Generate the draft with placeholders.
            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session["collected_data"],
                contract_schema=contract_schema,
            )
            session["pending_draft_confirmation"] = False
            session["pending_finalization_missing_fields"] = []
            session["status"] = "completed"

            return {
                "reply": "There are no remaining empty required fields to ask. Your contract draft is ready with TBD placeholders where needed.",
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": [],
                "status": session["status"],
            }

        if user_confirmed_generate:
            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session["collected_data"],
                contract_schema=contract_schema,
            )
            session["pending_draft_confirmation"] = False
            session["pending_finalization_missing_fields"] = []
            session["status"] = "completed"

            return {
                "reply": "Your contract draft is ready.",
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": pending_fields,
                "status": session["status"],
            }

        session["status"] = "awaiting_confirmation"
        return {
            "reply": (
                "Some required details are still missing or marked as TBD. "
                "If you want, I can generate the draft with TBD placeholders, "
                "or you can provide the missing details first."
            ),
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": pending_fields,
            "status": session["status"],
        }

    if user_intent in ["request_draft", "confirm_generate"]:
        if ready_to_finalize:
            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session["collected_data"],
                contract_schema=contract_schema,
            )
            session["status"] = "completed"
            session["pending_draft_confirmation"] = False
            session["pending_finalization_missing_fields"] = []

            return {
                "reply": "Your contract draft is ready.",
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": [],
                "status": session["status"],
            }

        session["pending_draft_confirmation"] = True
        session["pending_finalization_missing_fields"] = finalization_missing_fields
        session["status"] = "awaiting_confirmation"

        missing_readable = ", ".join(field.replace("_", " ") for field in finalization_missing_fields[:5])
        if len(finalization_missing_fields) > 5:
            missing_readable += ", and more"

        return {
            "reply": (
                "Your contract is not fully complete yet. "
                f"The following required details are still missing or marked as TBD: {missing_readable}. "
                "If you want, I can generate the draft now with TBD placeholders, "
                "or you can provide the missing details first."
            ),
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": finalization_missing_fields,
            "status": session["status"],
        }

    # If all genuinely empty required fields are handled, do not ask TBD fields again.
    # Generate a draft with placeholders for TBD fields.
    if ready_to_draft:
        draft = await generate_contract_draft_from_chat_with_model(
            contract_type=current_type,
            language=language,
            tone=tone,
            context=context,
            answers=session["collected_data"],
            contract_schema=contract_schema,
        )
        session["status"] = "completed"
        session["pending_draft_confirmation"] = False
        session["pending_finalization_missing_fields"] = []

        return {
            "reply": "Your contract draft is ready.",
            "draft": draft,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session["status"],
        }

    if session.get("pending_finalization_missing_fields"):
        updated_pending = [
            field for field in session.get("pending_finalization_missing_fields", [])
            if field in get_missing_required_fields(contract_schema, session["collected_data"])
        ]
        session["pending_finalization_missing_fields"] = updated_pending

    # For choosing the next question, use only genuinely missing fields.
    # Do NOT use pending_finalization_missing_fields here, because it can include TBD fields.
    active_missing_fields = missing_fields

    if not active_missing_fields:
        # No genuinely empty required fields remain.
        # Any remaining incomplete fields are likely TBD, so do not ask them again.
        draft = await generate_contract_draft_from_chat_with_model(
            contract_type=current_type,
            language=language,
            tone=tone,
            context=context,
            answers=session["collected_data"],
            contract_schema=contract_schema,
        )

        session["status"] = "completed"
        session["pending_draft_confirmation"] = False
        session["pending_finalization_missing_fields"] = []

        return {
            "reply": "Your contract draft is ready.",
            "draft": draft,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session["status"],
        }

    next_field = active_missing_fields[0]
    session["last_requested_fields"] = [next_field]

    next_question = await generate_next_chat_question_with_model(
        contract_type=current_type,
        contract_schema=contract_schema,
        next_field=next_field,
        collected_data=session["collected_data"],
        language=language,
    )

    session["status"] = "collecting_info"
    session["last_missing_prompt"] = next_question

    return {
        "reply": next_question,
        "draft": None,
        "session": session,
        "detected_contract_type": current_type,
        "missing_fields": missing_fields,
        "status": session["status"],
    }
