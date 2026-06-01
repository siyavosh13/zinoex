import os
import json
import re
from typing import Dict, Optional, List, Any, Tuple
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=300.0)


SUPPORTED_LANGUAGES = {"en", "fr"}


CONTRACT_ASSISTANT_SYSTEM_RULES = """
You are a professional contract drafting assistant.

Core scope:
- You only assist with contract-related tasks.
- You can help with:
  1. identifying contract types,
  2. collecting missing contract information,
  3. drafting contracts,
  4. revising contract drafts,
  5. improving contract language,
  6. explaining contract clauses,
  7. generating final contract drafts based on collected information.

Language rules:
- You only support English and French.
- If the user writes in English, respond in English.
- If the user writes in French, respond in French.
- If the user writes in any language other than English or French, politely refuse and ask the user to continue in English or French.
- Do not draft contracts in any language other than English or French.

Out-of-scope rules:
- If the user asks something unrelated to contracts, contract clauses, contract drafting, contract review, contract negotiation, or legal document preparation, do not answer the question.
- Politely explain that you can only assist with contract creation and contract-related tasks.
- Do not provide general knowledge answers, coding help, medical advice, personal advice, entertainment content, or unrelated explanations.
- Redirect the user back to contract creation, contract review, or contract revision.

Contract drafting rules:
- When generating a final contract draft, produce a detailed, comprehensive, professional legal-style contract unless the user explicitly requests a short version.
- Do not generate a short summary when the user expects a final contract.
- The final contract should be well-structured with clear headings and numbered clauses.
- Use formal legal drafting style.
- Include relevant clauses whenever applicable, such as:
  1. Title,
  2. Date,
  3. Parties,
  4. Background / Recitals,
  5. Definitions,
  6. Purpose or Scope,
  7. Obligations of each party,
  8. Deliverables or services,
  9. Payment terms,
  10. Taxes and expenses,
  11. Term and duration,
  12. Renewal, if applicable,
  13. Termination,
  14. Confidentiality,
  15. Intellectual property,
  16. Data protection, privacy, or security obligations, if applicable,
  17. Representations and warranties,
  18. Disclaimers,
  19. Liability and limitation of liability,
  20. Indemnification, if applicable,
  21. Force majeure,
  22. Compliance with laws,
  23. Non-solicitation or non-compete, if applicable and requested,
  24. Dispute resolution,
  25. Governing law and jurisdiction,
  26. Notices,
  27. Assignment,
  28. Severability,
  29. Waiver,
  30. Entire agreement,
  31. Amendments,
  32. Counterparts and electronic signatures,
  33. Signature blocks.
- Do not invent critical facts that the user has not provided.
- If a detail is unknown, either use a clear placeholder such as [Insert Name], [Insert Date], or [Insert Jurisdiction], or ask a follow-up question if needed.

Information collection rules:
- If required information is missing, ask concise and relevant follow-up questions.
- Do not ask too many questions at once unless necessary.
- Use the existing collected session data whenever available.
- Do not repeatedly ask for information that has already been provided.
- Never get stuck repeating the same unanswered question in a loop.
- If the user gives an unclear, indirect, approximate, partial, or not perfectly structured answer to the last asked field, interpret it as best as possible or store it as the answer for that field instead of repeating the same question endlessly.
- If the user skips a field, marks it as TBD, says they do not know, or answers irrelevantly after the field was already asked, move forward instead of asking the exact same question again and again.
- If the user asks to generate the contract and enough information is available, generate the draft.
- If important information is missing, ask for the missing fields before finalizing.

Safety and accuracy:
- Do not claim to be a licensed attorney.
- Do not guarantee legal enforceability.
- You may include a short note that the draft should be reviewed by a qualified legal professional where appropriate.
"""


def normalize_supported_language(language: Optional[str]) -> str:
    value = (language or "en").strip().lower()

    if value in SUPPORTED_LANGUAGES:
        return value

    return "en"


def is_language_supported(language: Optional[str]) -> bool:
    value = (language or "en").strip().lower()
    return value in SUPPORTED_LANGUAGES


def unsupported_language_reply(language: Optional[str] = "en") -> str:
    normalized = normalize_supported_language(language)

    if normalized == "fr":
        return "Désolé, je prends actuellement en charge uniquement l’anglais et le français pour la rédaction de contrats. Veuillez continuer en anglais ou en français."

    return "Sorry, I currently support only English and French for contract drafting. Please continue in English or French."


def contract_ready_reply(language: Optional[str] = "en") -> str:
    normalized = normalize_supported_language(language)

    if normalized == "fr":
        return "Votre projet de contrat est prêt."

    return "Your contract draft is ready."


def default_contract_type_question(language: Optional[str] = "en") -> str:
    normalized = normalize_supported_language(language)

    if normalized == "fr":
        return "Quel type de contrat souhaitez-vous que je vous aide à rédiger ?"

    return "What type of contract would you like me to help you draft?"


def is_refusal_or_out_of_scope_reply(reply: str) -> bool:
    if not reply:
        return False

    lower_reply = reply.lower()

    refusal_markers = [
        "only assist with contract",
        "only support contract",
        "only help with contract",
        "only contract-related",
        "contract-related assistance",
        "contract creation",
        "contract drafting",
        "english and french",
        "only english and french",
        "continue in english or french",
        "je prends actuellement en charge uniquement",
        "uniquement l’anglais et le français",
        "uniquement l'anglais et le français",
        "assistance liée aux contrats",
        "rédaction de contrats",
    ]

    return any(marker in lower_reply for marker in refusal_markers)


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
        return "long"

    value = str(value).strip().lower()

    if value in ["short"]:
        return "short"

    if value in ["medium", "normal", "standard"]:
        return "medium"

    if value in ["long", "detailed", "full", "comprehensive", "complete"]:
        return "long"

    return "long"


def get_contract_length(answers: Dict) -> str:
    if not answers:
        return "long"

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

    return "long"


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

    language = normalize_supported_language(language)

    contract_length = get_contract_length(answers)
    length_instruction = get_contract_length_instruction(contract_length)
    max_output_tokens = get_max_output_tokens_by_length(contract_length)

    system_prompt = f"""
{CONTRACT_ASSISTANT_SYSTEM_RULES}

You are generating a final contract draft.

Additional drafting requirements:
- Follow the requested contract length carefully.
- Return a full contract, not a summary.
- The draft must be legally coherent, complete, detailed, and professionally structured.
- Unless the user explicitly selected a short version, generate a detailed and comprehensive agreement.
- If the selected length is long, make the agreement highly detailed and comprehensive.
- If the selected length is medium, make it balanced and complete.
- If the selected length is short, keep it concise but still usable.
- Use the provided answers as the primary factual source.
- If some important details are missing, unclear, skipped, or marked as TBD, do not refuse to generate the contract.
- Use the available information accurately and insert professional placeholders where information is missing.
- If some important details are missing, use placeholders instead of making up facts.
- Only generate the contract in English or French.
"""

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
- Do not ignore the selected contract length.
- If important information is missing, use clear placeholders instead of inventing facts.
- Use professional legal formatting with clear headings.
- Use numbered clauses and subclauses where appropriate.
- Unless a short contract was explicitly selected, make the contract detailed, complete, and professionally drafted.
- If any field is incomplete, skipped, or marked TBD, still generate the contract using professional placeholders where needed.
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
    language = normalize_supported_language(language)
    contract_text = text[:50000]

    try:
        messages = [
            {
                "role": "system",
                "content": f"""
{CONTRACT_ASSISTANT_SYSTEM_RULES}

You are an AI contract analyzer.
Return ONLY pure JSON.
Only analyze contracts and contract-related legal documents.
"""
            },
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


def looks_like_skip_request(text: str) -> bool:
    if not text:
        return False

    t = normalize_text(text).lower()

    skip_phrases = [
        "skip",
        "skip it",
        "skip this",
        "please skip",
        "please skip this",
        "leave blank",
        "leave it blank",
        "leave this blank",
        "leave it empty",
        "blank",
        "tbd",
        "later",
        "unknown",
        "not sure",
        "i don't know",
        "i dont know",
        "don't know",
        "dont know",
        "do not know",
        "no idea",
        "prefer not to say",
        "prefer not to answer",
        "decide later",
        "fill later",
        "to be decided",
        "for now leave it blank",
        "leave it for now",
        "for now skip it",
        "not now",
        "answer later",
        "i will answer later",
        "we can decide later",
        "let's skip this",
        "lets skip this",
        "move on",
        "go to the next question",
        "next question",
        "ask me later",
    ]

    return any(phrase in t for phrase in skip_phrases)


def is_affirmative(text: str) -> bool:
    t = normalize_text(text).strip().lower()
    yes_values = {
        "yes", "y", "yeah", "yep", "sure", "ok", "okay",
        "please do", "go ahead", "continue", "ask again",
        "yes please"
    }
    return t in yes_values


def is_negative(text: str) -> bool:
    t = normalize_text(text).strip().lower()

    no_values = [
        "no",
        "n",
        "nope",
        "nah",
        "not now",
        "skip",
        "don't ask",
        "do not ask",
        "continue without it",
        "go without it",
        "no thanks",
        "generate with current information",
        "generate the contract with current information",
        "use current information",
        "use the current information",
        "generate now",
        "generate it now",
        "proceed with current information",
        "proceed without it",
        "create it now",
        "create the contract now",
        "generate anyway",
        "continue anyway",
        "use what you have",
    ]

    return any(value in t for value in no_values)


def incomplete_fields_confirmation_reply(incomplete_fields: List[str], language: str = "en") -> str:
    language = normalize_supported_language(language)
    field_list = ", ".join(incomplete_fields)

    if language == "fr":
        return (
            "Certaines informations requises sont encore incomplètes ou laissées vides : "
            f"{field_list}. "
            "Souhaitez-vous que je repose les questions restées sans réponse afin de les compléter ? "
            "Ces informations sont utiles pour préparer un contrat plus précis. "
            "Répondez par oui pour continuer, ou par non pour générer le contrat avec les informations actuelles."
        )

    return (
        "Some required information is still incomplete or left blank: "
        f"{field_list}. "
        "Would you like me to ask the unanswered questions again so you can complete them? "
        "These details are useful for preparing a more accurate contract. "
        "Reply yes to continue, or no to generate the contract with the current information."
    )


def is_placeholder_value(value: Any) -> bool:
    if value is None:
        return True

    value = normalize_text(value).strip().lower()
    if not value:
        return True

    placeholders = {
        "n/a", "na", "unknown", "not sure", "skip",
        "[insert]", "later", "placeholder"
    }
    return value in placeholders


def get_schema_fields(contract_schema: Dict[str, Any]) -> List[str]:
    if not contract_schema:
        return []
    return list(contract_schema.get("required_fields", [])) + list(contract_schema.get("optional_fields", []))


def get_missing_required_fields(contract_schema: Dict[str, Any], collected_data: Dict[str, Any]) -> List[str]:
    if not contract_schema:
        return []

    missing = []
    for field in contract_schema.get("required_fields", []):
        value = collected_data.get(field)

        if normalize_text(value).upper() == "TBD":
            continue

        if is_placeholder_value(value):
            missing.append(field)

    return missing


def get_incomplete_required_fields(
    contract_schema: Dict[str, Any],
    collected_data: Dict[str, Any],
    include_tbd: bool = False,
) -> List[str]:
    if not contract_schema:
        return []

    incomplete = []
    for field in contract_schema.get("required_fields", []):
        value = collected_data.get(field)

        if value is None:
            incomplete.append(field)
            continue

        normalized_value = normalize_text(value)
        if not normalized_value:
            incomplete.append(field)
            continue

        if normalized_value.upper() == "TBD":
            if include_tbd:
                incomplete.append(field)
            continue

        if is_placeholder_value(value):
            incomplete.append(field)
            continue

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


def is_control_message_for_contract_flow(text: str) -> bool:
    if not text:
        return False

    t = normalize_text(text).strip().lower()

    control_phrases = [
        "generate",
        "generate now",
        "generate it now",
        "generate anyway",
        "create contract",
        "create the contract",
        "draft it",
        "use what you have",
        "continue anyway",
        "proceed",
        "proceed anyway",
        "next",
        "next question",
        "move on",
        "skip",
        "skip this",
        "skip it",
        "leave blank",
        "leave it blank",
        "tbd",
        "not now",
        "fill missing",
        "ask unanswered questions again",
    ]

    return any(phrase == t or phrase in t for phrase in control_phrases)


def pick_next_missing_field(contract_schema: Dict[str, Any], collected_data: Dict[str, Any]) -> Optional[str]:
    missing_fields = get_missing_required_fields(contract_schema, collected_data)
    if not missing_fields:
        return None
    return missing_fields[0]


def apply_last_requested_field_fallback(
    user_message: str,
    session: Dict[str, Any],
    extracted_data: Dict[str, Any],
    fields_to_mark_tbd: List[str],
    allowed_fields: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    extracted_data = extracted_data or {}
    fields_to_mark_tbd = fields_to_mark_tbd or []

    last_requested_fields = session.get("last_requested_fields", []) or []
    if not last_requested_fields:
        return extracted_data, fields_to_mark_tbd

    target_field = last_requested_fields[0]

    if allowed_fields and target_field not in allowed_fields:
        return extracted_data, fields_to_mark_tbd

    if target_field in extracted_data:
        return extracted_data, fields_to_mark_tbd

    if target_field in fields_to_mark_tbd:
        return extracted_data, fields_to_mark_tbd

    user_text = normalize_text(user_message)
    if not user_text:
        return extracted_data, fields_to_mark_tbd

    if looks_like_skip_request(user_text):
        updated_tbd = list(fields_to_mark_tbd)
        if target_field not in updated_tbd:
            updated_tbd.append(target_field)
        return extracted_data, updated_tbd

    if is_control_message_for_contract_flow(user_text):
        return extracted_data, fields_to_mark_tbd

    updated = dict(extracted_data)
    updated[target_field] = user_text
    return updated, fields_to_mark_tbd


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
        "awaiting_incomplete_fields_confirmation": session.get("awaiting_incomplete_fields_confirmation", False),
        "pending_incomplete_fields": session.get("pending_incomplete_fields", []),
    }

    system_prompt = f"""
{CONTRACT_ASSISTANT_SYSTEM_RULES}

You are an AI assistant for a contract-generation chatbot.

Your job:
- Understand the user's goal.
- Detect the most appropriate contract type from the provided CONTRACT_SCHEMAS.
- Extract any structured data the user provides for contract fields.
- Decide whether the user is answering a previous question, starting a new contract, asking for the draft, asking a contract-related question, asking a general unrelated question, or asking to skip a field.

Important scope rules:
- The chatbot is only for contract creation, contract drafting, contract review, contract revision, and contract-related questions.
- If the user asks anything unrelated to contracts or legal document preparation, do not answer the actual question.
- For unrelated messages, set intent to "ask_question", contract_type to null unless already known from the session, extracted_data to {{}}, and assistant_reply to a polite refusal.
- The refusal should say that you only assist with contract drafting and contract-related tasks.
- If the user writes in a language other than English or French, set intent to "ask_question" and assistant_reply should politely say that only English and French are supported.

Rules:
- Return ONLY valid JSON.
- Do not invent contract types outside the schema.
- Keep assistant_reply concise and helpful.
- If contract type is unclear, set contract_type to null.
- fields_to_mark_tbd should include fields the user wants to skip, leave blank, or decide later.
- extracted_data should only include data actually provided by the user.
- If the user is clearly answering the previously requested field, map the answer to that field whenever possible.
- If the user says things like "leave it blank", "skip", "later", or "TBD", mark the most recently requested field in fields_to_mark_tbd.
- If the user wants to complete unanswered or previously skipped fields, set intent to "fill_missing".
- If the last asked field is still unanswered and the user gives a vague, partial, approximate, indirect, or not perfectly structured answer, prefer mapping that answer to the last requested field rather than leaving extracted_data empty.
- Never cause a loop by leaving the last requested field unresolved when the user has already replied.
- If the user reply is not a clear control instruction and there is a last requested field, try to interpret the reply as an answer to that field.
- Do not answer general knowledge, coding, medical, entertainment, personal, or unrelated questions.
- If the user's message is contract-related but incomplete, ask for clarification through assistant_reply.
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

        return {
            "intent": parsed.get("intent", "unclear"),
            "contract_type": parsed.get("contract_type"),
            "confidence": parsed.get("confidence", 0.0),
            "extracted_data": parsed.get("extracted_data", {}) or {},
            "fields_to_mark_tbd": parsed.get("fields_to_mark_tbd", []) or [],
            "assistant_reply": parsed.get("assistant_reply", "") or "",
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
    language = normalize_supported_language(language)

    system_prompt = f"""
{CONTRACT_ASSISTANT_SYSTEM_RULES}

You are an AI contract assistant collecting information for a contract.
Ask only ONE clear and concise question.
Do not ask multiple questions at once.
Do not provide legal advice.
Only ask questions needed to complete the contract.
Do not repeat the exact same unanswered question in a loop if the user already replied and the system has decided to move on.
Respond only in English or French.
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

        if language == "fr":
            return f"Pourriez-vous fournir les informations suivantes : {readable} ?"

        return f"Could you please provide the {readable}?"


async def generate_contract_draft_from_chat_with_model(
    contract_type: str,
    language: str,
    tone: str,
    context: str,
    answers: Dict[str, Any],
    contract_schema: Optional[Dict[str, Any]] = None,
) -> str:
    language = normalize_supported_language(language)

    final_answers = dict(answers or {})
    contract_schema = contract_schema or {}

    all_fields = get_schema_fields(contract_schema)
    for field in all_fields:
        if field not in final_answers or is_placeholder_value(final_answers.get(field)) or normalize_text(final_answers.get(field)).upper() == "TBD":
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
    raw_language = language

    if not is_language_supported(raw_language):
        if session is None:
            session = {}

        session["status"] = "unsupported_language"

        return {
            "reply": unsupported_language_reply(raw_language),
            "draft": None,
            "session": session,
            "detected_contract_type": session.get("detected_contract_type"),
            "missing_fields": [],
            "status": session["status"],
        }

    language = normalize_supported_language(language)

    if session is None:
        session = {}

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

    current_type = session.get("detected_contract_type")
    contract_schema = contract_schemas.get(current_type) if current_type in contract_schemas else None

    if session.get("awaiting_incomplete_fields_confirmation") and current_type and contract_schema:
        if is_affirmative(user_message):
            pending_fields = session.get("pending_incomplete_fields", []) or []
            current_incomplete_fields = get_incomplete_required_fields(
                contract_schema,
                session.get("collected_data", {}),
                include_tbd=True,
            )

            session["awaiting_incomplete_fields_confirmation"] = False
            session["allow_generation_with_incomplete"] = False

            pending_fields = [
                field for field in pending_fields
                if field in current_incomplete_fields
            ]

            session["pending_incomplete_fields"] = pending_fields

            if pending_fields:
                next_field = pending_fields[0]
                session["last_requested_fields"] = [next_field]
                session["status"] = "collecting_info"

                next_question = await generate_next_chat_question_with_model(
                    contract_type=current_type,
                    contract_schema=contract_schema,
                    next_field=next_field,
                    collected_data=session.get("collected_data", {}),
                    language=language,
                )

                return {
                    "reply": next_question,
                    "draft": None,
                    "session": session,
                    "detected_contract_type": current_type,
                    "missing_fields": pending_fields,
                    "status": session["status"],
                }

            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session.get("collected_data", {}),
                contract_schema=contract_schema,
            )

            session["status"] = "completed"
            session["awaiting_incomplete_fields_confirmation"] = False
            session["pending_incomplete_fields"] = []
            session["last_requested_fields"] = []

            return {
                "reply": contract_ready_reply(language),
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": [],
                "status": session["status"],
            }

        if is_negative(user_message):
            session["awaiting_incomplete_fields_confirmation"] = False
            session["allow_generation_with_incomplete"] = True
            session["pending_incomplete_fields"] = []
            session["last_requested_fields"] = []

            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session.get("collected_data", {}),
                contract_schema=contract_schema,
            )

            session["status"] = "completed"
            session["awaiting_incomplete_fields_confirmation"] = False
            session["pending_incomplete_fields"] = []
            session["last_requested_fields"] = []

            return {
                "reply": contract_ready_reply(language),
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": [],
                "status": session["status"],
            }

        if language == "fr":
            clarification_reply = (
                "Veuillez répondre par oui si vous souhaitez compléter les questions sans réponse, "
                "ou par non si vous souhaitez générer le contrat avec les informations actuelles."
            )
        else:
            clarification_reply = (
                "Please reply yes if you want to complete the unanswered questions, "
                "or no if you want me to generate the contract with the current information."
            )

        return {
            "reply": clarification_reply,
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": session.get("pending_incomplete_fields", []),
            "status": session.get("status", "collecting_info"),
        }

    current_type = session.get("detected_contract_type")
    contract_schema = contract_schemas.get(current_type) if current_type in contract_schemas else None

    if current_type and contract_schema and looks_like_skip_request(user_message):
        last_requested_fields = session.get("last_requested_fields", []) or []

        if last_requested_fields:
            skipped_field = last_requested_fields[0]
            session["collected_data"][skipped_field] = "TBD"

            current_incomplete_with_tbd = get_incomplete_required_fields(
                contract_schema,
                session["collected_data"],
                include_tbd=True,
            )

            if session.get("pending_incomplete_fields"):
                session["pending_incomplete_fields"] = [
                    field for field in session.get("pending_incomplete_fields", [])
                    if field in current_incomplete_with_tbd
                ]

            next_field = pick_next_missing_field(contract_schema, session["collected_data"])

            if next_field:
                session["last_requested_fields"] = [next_field]
                session["status"] = "collecting_info"
                session["awaiting_incomplete_fields_confirmation"] = False

                next_question = await generate_next_chat_question_with_model(
                    contract_type=current_type,
                    contract_schema=contract_schema,
                    next_field=next_field,
                    collected_data=session["collected_data"],
                    language=language,
                )

                return {
                    "reply": next_question,
                    "draft": None,
                    "session": session,
                    "detected_contract_type": current_type,
                    "missing_fields": get_missing_required_fields(contract_schema, session["collected_data"]),
                    "status": session["status"],
                }

            incomplete_fields = get_incomplete_required_fields(
                contract_schema,
                session["collected_data"],
                include_tbd=False,
            )

            if incomplete_fields and not session.get("allow_generation_with_incomplete", False):
                session["awaiting_incomplete_fields_confirmation"] = True
                session["pending_incomplete_fields"] = incomplete_fields
                session["last_requested_fields"] = []
                session["status"] = "awaiting_incomplete_fields_confirmation"

                return {
                    "reply": incomplete_fields_confirmation_reply(incomplete_fields, language),
                    "draft": None,
                    "session": session,
                    "detected_contract_type": current_type,
                    "missing_fields": incomplete_fields,
                    "status": session["status"],
                }

            draft = await generate_contract_draft_from_chat_with_model(
                contract_type=current_type,
                language=language,
                tone=tone,
                context=context,
                answers=session["collected_data"],
                contract_schema=contract_schema,
            )

            session["status"] = "completed"
            session["awaiting_incomplete_fields_confirmation"] = False
            session["pending_incomplete_fields"] = []
            session["last_requested_fields"] = []

            return {
                "reply": contract_ready_reply(language),
                "draft": draft,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": [],
                "status": session["status"],
            }

    analysis = await analyze_contract_chat_with_model(
        user_message=user_message,
        session=session,
        contract_schemas=contract_schemas,
    )

    valid_contract_types = set(contract_schemas.keys())
    detected_type = analysis.get("contract_type")
    current_type = session.get("detected_contract_type")

    if detected_type in valid_contract_types:
        current_type = detected_type
        session["detected_contract_type"] = detected_type

    contract_schema = contract_schemas.get(current_type) if current_type in contract_schemas else None
    allowed_fields = get_schema_fields(contract_schema) if contract_schema else None

    extracted_data = analysis.get("extracted_data", {}) or {}
    fields_to_mark_tbd = analysis.get("fields_to_mark_tbd", []) or []

    extracted_data, fields_to_mark_tbd = apply_last_requested_field_fallback(
        user_message=user_message,
        session=session,
        extracted_data=extracted_data,
        fields_to_mark_tbd=fields_to_mark_tbd,
        allowed_fields=allowed_fields,
    )

    merged_data = merge_extracted_data(
        existing=session.get("collected_data", {}),
        new_data=extracted_data,
        allowed_fields=allowed_fields,
    )

    for field in fields_to_mark_tbd:
        if allowed_fields and field in allowed_fields:
            merged_data[field] = "TBD"
        elif not allowed_fields:
            merged_data[field] = "TBD"

    session["collected_data"] = merged_data

    user_intent = analysis.get("intent", "unclear")
    assistant_reply = analysis.get("assistant_reply", "") or ""

    if current_type and contract_schema:
        current_incomplete_without_tbd = get_incomplete_required_fields(
            contract_schema,
            session["collected_data"],
            include_tbd=False,
        )
        current_incomplete_with_tbd = get_incomplete_required_fields(
            contract_schema,
            session["collected_data"],
            include_tbd=True,
        )

        if session.get("pending_incomplete_fields"):
            session["pending_incomplete_fields"] = [
                field for field in session.get("pending_incomplete_fields", [])
                if field in current_incomplete_with_tbd
            ]

        if session.get("last_requested_fields"):
            session["last_requested_fields"] = [
                field for field in session.get("last_requested_fields", [])
                if field in current_incomplete_with_tbd or field in get_missing_required_fields(contract_schema, session["collected_data"])
            ]

        if (
            session.get("last_requested_fields")
            and normalize_text(user_message)
            and not looks_like_skip_request(user_message)
            and not is_control_message_for_contract_flow(user_message)
        ):
            answered_field = session["last_requested_fields"][0]
            if answered_field in session["collected_data"]:
                answered_value = normalize_text(session["collected_data"].get(answered_field))
                if answered_value and answered_value.upper() != "TBD":
                    remaining_last_requested = [
                        field for field in session.get("last_requested_fields", [])
                        if field != answered_field and field in current_incomplete_with_tbd
                    ]
                    session["last_requested_fields"] = remaining_last_requested

        if not current_incomplete_without_tbd and not session.get("awaiting_incomplete_fields_confirmation"):
            session["pending_incomplete_fields"] = []

    if user_intent == "ask_question" and assistant_reply and is_refusal_or_out_of_scope_reply(assistant_reply):
        if not current_type or not contract_schema:
            session["status"] = "awaiting_contract_type"
        else:
            session["status"] = session.get("status", "collecting_info")

        return {
            "reply": assistant_reply,
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session["status"],
        }

    if not current_type or not contract_schema:
        session["status"] = "awaiting_contract_type"
        return {
            "reply": analysis.get("assistant_reply") or default_contract_type_question(language),
            "draft": None,
            "session": session,
            "detected_contract_type": None,
            "missing_fields": [],
            "status": session["status"],
        }

    if user_intent == "fill_missing":
        incomplete_fields = get_incomplete_required_fields(
            contract_schema,
            session["collected_data"],
            include_tbd=True,
        )

        if incomplete_fields:
            session["awaiting_incomplete_fields_confirmation"] = False
            session["allow_generation_with_incomplete"] = False
            session["pending_incomplete_fields"] = incomplete_fields
            session["last_requested_fields"] = [incomplete_fields[0]]
            session["status"] = "collecting_info"

            next_question = await generate_next_chat_question_with_model(
                contract_type=current_type,
                contract_schema=contract_schema,
                next_field=incomplete_fields[0],
                collected_data=session["collected_data"],
                language=language,
            )

            return {
                "reply": next_question,
                "draft": None,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": incomplete_fields,
                "status": session["status"],
            }

        if language == "fr":
            no_missing_reply = "Toutes les informations requises disponibles ont déjà été complétées."
        else:
            no_missing_reply = "All available required information has already been completed."

        return {
            "reply": no_missing_reply,
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session.get("status", "completed"),
        }

    missing_fields = get_missing_required_fields(contract_schema, session["collected_data"])

    if user_intent == "ask_question" and assistant_reply and is_refusal_or_out_of_scope_reply(assistant_reply):
        session["status"] = "collecting_info" if missing_fields else session.get("status", "completed")

        return {
            "reply": assistant_reply,
            "draft": None,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": missing_fields,
            "status": session["status"],
        }

    if user_intent in ["request_draft", "confirm_generate"] and not missing_fields:
        incomplete_fields = get_incomplete_required_fields(
            contract_schema,
            session["collected_data"],
            include_tbd=False,
        )

        if incomplete_fields and not session.get("allow_generation_with_incomplete", False):
            session["awaiting_incomplete_fields_confirmation"] = True
            session["pending_incomplete_fields"] = incomplete_fields
            session["last_requested_fields"] = []
            session["status"] = "awaiting_incomplete_fields_confirmation"

            return {
                "reply": incomplete_fields_confirmation_reply(incomplete_fields, language),
                "draft": None,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": incomplete_fields,
                "status": session["status"],
            }

        draft = await generate_contract_draft_from_chat_with_model(
            contract_type=current_type,
            language=language,
            tone=tone,
            context=context,
            answers=session["collected_data"],
            contract_schema=contract_schema,
        )

        session["status"] = "completed"
        session["awaiting_incomplete_fields_confirmation"] = False
        session["pending_incomplete_fields"] = []
        session["last_requested_fields"] = []

        return {
            "reply": contract_ready_reply(language),
            "draft": draft,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session["status"],
        }

    if not missing_fields:
        incomplete_fields = get_incomplete_required_fields(
            contract_schema,
            session["collected_data"],
            include_tbd=False,
        )

        if incomplete_fields and not session.get("allow_generation_with_incomplete", False):
            session["awaiting_incomplete_fields_confirmation"] = True
            session["pending_incomplete_fields"] = incomplete_fields
            session["last_requested_fields"] = []
            session["status"] = "awaiting_incomplete_fields_confirmation"

            return {
                "reply": incomplete_fields_confirmation_reply(incomplete_fields, language),
                "draft": None,
                "session": session,
                "detected_contract_type": current_type,
                "missing_fields": incomplete_fields,
                "status": session["status"],
            }

        draft = await generate_contract_draft_from_chat_with_model(
            contract_type=current_type,
            language=language,
            tone=tone,
            context=context,
            answers=session["collected_data"],
            contract_schema=contract_schema,
        )

        session["status"] = "completed"
        session["awaiting_incomplete_fields_confirmation"] = False
        session["pending_incomplete_fields"] = []
        session["last_requested_fields"] = []

        return {
            "reply": contract_ready_reply(language),
            "draft": draft,
            "session": session,
            "detected_contract_type": current_type,
            "missing_fields": [],
            "status": session["status"],
        }

    next_field = missing_fields[0]
    session["last_requested_fields"] = [next_field]
    session["status"] = "collecting_info"

    next_question = await generate_next_chat_question_with_model(
        contract_type=current_type,
        contract_schema=contract_schema,
        next_field=next_field,
        collected_data=session["collected_data"],
        language=language,
    )

    return {
        "reply": next_question,
        "draft": None,
        "session": session,
        "detected_contract_type": current_type,
        "missing_fields": missing_fields,
        "status": session["status"],
    }
