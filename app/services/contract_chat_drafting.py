# app/services/contract_chat_drafting.py

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.contract_clause_library import (
    Clause,
    get_clauses_for_contract,
    render_all_clauses,
)
from app.services.contract_field_rules import (
    get_missing_required_fields,
    is_ready_for_drafting,
    normalize_collected_fields,
)
from app.services.contract_registry import (
    get_contract_definition,
    is_supported_contract_type,
)


# ---------------------------------------------------------------------
# Basic formatting helpers
# ---------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """
    Clean extra whitespace while preserving paragraph structure.
    """
    if not text:
        return ""

    lines = [line.strip() for line in text.strip().splitlines()]
    cleaned_lines = []

    previous_blank = False

    for line in lines:
        if line == "":
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()


def _format_contract_title(title: str) -> str:
    """
    Format contract title as uppercase.
    """
    return title.upper().strip()


def _format_effective_date(fields: Dict[str, Any]) -> str:
    """
    Determine the best effective date value from available fields.
    """
    possible_keys = [
        "effective_date",
        "start_date",
        "commencement_date",
        "agreement_date",
        "execution_date",
    ]

    for key in possible_keys:
        value = fields.get(key)
        if value:
            return str(value)

    return datetime.utcnow().strftime("%B %d, %Y")


def _format_parties_line(fields: Dict[str, Any]) -> Optional[str]:
    """
    Try to create a general parties line based on common field names.
    This is intentionally flexible because different contracts use different party names.
    """

    party_pairs = [
        ("employer_name", "employee_name", "Employer", "Employee"),
        ("client_name", "freelancer_name", "Client", "Freelancer"),
        ("client_name", "consultant_name", "Client", "Consultant"),
        ("service_provider_name", "client_name", "Service Provider", "Client"),
        ("landlord_name", "tenant_name", "Landlord", "Tenant"),
        ("seller_name", "buyer_name", "Seller", "Buyer"),
        ("lender_name", "borrower_name", "Lender", "Borrower"),
        ("licensor_name", "licensee_name", "Licensor", "Licensee"),
        ("disclosing_party", "receiving_party", "Disclosing Party", "Receiving Party"),
        ("party_one", "party_two", "Party One", "Party Two"),
    ]

    for left_key, right_key, left_label, right_label in party_pairs:
        left_value = fields.get(left_key)
        right_value = fields.get(right_key)

        if left_value and right_value:
            return (
                f"This Agreement is entered into by and between "
                f"{left_value} (the \"{left_label}\") and "
                f"{right_value} (the \"{right_label}\")."
            )

    return None


def _format_field_label(field_key: str) -> str:
    """
    Convert snake_case field keys into readable labels.
    """
    return field_key.replace("_", " ").title()


def _format_governing_law(value: Any) -> str:
    """
    Normalize governing law value for use in clauses.

    Examples:
    - "Ontario" -> "the laws of Ontario"
    - "the laws of Ontario" -> "the laws of Ontario"
    - "laws of Ontario" -> "the laws of Ontario"
    - "law of Ontario" -> "the law of Ontario"
    """

    if value is None or str(value).strip() == "":
        return "the applicable laws"

    text = str(value).strip()
    lowered = text.lower()

    if lowered.startswith("the laws of "):
        return text

    if lowered.startswith("laws of "):
        return f"the {text}"

    if lowered.startswith("the law of "):
        return text

    if lowered.startswith("law of "):
        return f"the {text}"

    return f"the laws of {text}"


# ---------------------------------------------------------------------
# Draft validation helpers
# ---------------------------------------------------------------------

def get_drafting_readiness(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Return whether a contract can be drafted and why.
    """

    fields = normalize_collected_fields(fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    if not contract_type:
        return {
            "ready": False,
            "reason": "missing_contract_type",
            "message": "Contract type is missing.",
            "missing_required_fields": [],
        }

    if not is_supported_contract_type(contract_type):
        return {
            "ready": False,
            "reason": "unsupported_contract_type",
            "message": f"Unsupported contract type: {contract_type}",
            "missing_required_fields": [],
        }

    missing_required = get_missing_required_fields(contract_type, fields)

    if missing_required:
        return {
            "ready": False,
            "reason": "missing_required_fields",
            "message": "Required information is missing.",
            "missing_required_fields": [
                {
                    "key": field.key,
                    "label": field.label,
                    "question": field.question,
                    "example": field.example,
                }
                for field in missing_required
            ],
        }

    return {
        "ready": True,
        "reason": "ready_for_drafting",
        "message": "The contract is ready for drafting.",
        "missing_required_fields": [],
    }


# ---------------------------------------------------------------------
# Clause rendering
# ---------------------------------------------------------------------

def get_rendered_clause_blocks(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Render all clauses for a contract type.
    """

    fields = normalize_collected_fields(fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    rendered_clauses = render_all_clauses(contract_type, fields)

    cleaned = []

    for clause in rendered_clauses:
        cleaned.append(
            {
                "key": clause.get("key", ""),
                "title": clause.get("title", ""),
                "text": _clean_text(clause.get("text", "")),
            }
        )

    return cleaned


def build_numbered_clause_text(rendered_clauses: List[Dict[str, str]]) -> str:
    """
    Convert rendered clauses into numbered contract sections.
    """

    sections = []

    for index, clause in enumerate(rendered_clauses, start=1):
        title = clause.get("title", "").strip()
        text = clause.get("text", "").strip()

        if not title and not text:
            continue

        if title:
            sections.append(f"{index}. {title}\n\n{text}")
        else:
            sections.append(f"{index}. {text}")

    return "\n\n".join(sections).strip()


# ---------------------------------------------------------------------
# Fallback drafting for unsupported clause-library types
# ---------------------------------------------------------------------

def build_fallback_clause_blocks(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Build a generic fallback draft if no dedicated clause library exists yet.
    This allows the system to produce a structured draft for supported contract
    types even before all specialized clauses are written.
    """

    fields = normalize_collected_fields(fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    definition = get_contract_definition(contract_type)

    title = definition.title if definition else _format_field_label(contract_type)

    parties_line = _format_parties_line(fields)

    introduction_text = parties_line or (
        f"This {title} is prepared based on the information provided by the parties."
    )

    purpose_value = (
        fields.get("purpose")
        or fields.get("project_description")
        or fields.get("services_description")
        or fields.get("transaction_description")
        or fields.get("business_purpose")
        or "the purpose described by the parties"
    )

    governing_law = _format_governing_law(fields.get("governing_law", "Canada"))

    field_summary_lines = []

    for key, value in fields.items():
        if value is None or str(value).strip() == "":
            continue

        field_summary_lines.append(f"- {_format_field_label(key)}: {value}")

    field_summary = "\n".join(field_summary_lines) if field_summary_lines else (
        "The material commercial terms shall be as agreed by the parties in writing."
    )

    return [
        {
            "key": "introduction",
            "title": "Introduction",
            "text": introduction_text,
        },
        {
            "key": "purpose",
            "title": "Purpose",
            "text": (
                f"The purpose of this Agreement is to set out the rights and "
                f"obligations of the parties in relation to {purpose_value}."
            ),
        },
        {
            "key": "commercial_terms",
            "title": "Commercial Terms",
            "text": (
                "The parties agree to the following material terms:\n\n"
                f"{field_summary}"
            ),
        },
        {
            "key": "confidentiality",
            "title": "Confidentiality",
            "text": (
                "Each party shall protect confidential information received from "
                "the other party and shall not disclose such information except as "
                "required for the performance of this Agreement or as required by law."
            ),
        },
        {
            "key": "representations",
            "title": "Representations and Authority",
            "text": (
                "Each party represents that it has the legal authority and capacity "
                "to enter into this Agreement and to perform its obligations under it."
            ),
        },
        {
            "key": "limitation_of_liability",
            "title": "Limitation of Liability",
            "text": (
                "To the maximum extent permitted by applicable law, neither party "
                "shall be liable for indirect, incidental, special, consequential, "
                "or punitive damages arising out of or relating to this Agreement."
            ),
        },
        {
            "key": "termination",
            "title": "Termination",
            "text": (
                "This Agreement may be terminated in accordance with its terms, by "
                "mutual written agreement of the parties, or as otherwise permitted "
                "by applicable law."
            ),
        },
        {
            "key": "governing_law",
            "title": "Governing Law",
            "text": (
                f"This Agreement shall be governed by and construed in accordance "
                f"with {governing_law}."
            ),
        },
    ]


# ---------------------------------------------------------------------
# Main draft generation
# ---------------------------------------------------------------------

def generate_contract_draft(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
    include_disclaimer: bool = True,
    use_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Generate a structured contract draft.

    Returns a dictionary suitable for API responses:
    {
        "success": bool,
        "contract_type": str,
        "title": str,
        "draft_text": str,
        "clauses": [...],
        "readiness": {...}
    }
    """

    fields = normalize_collected_fields(fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    readiness = get_drafting_readiness(contract_type, fields)

    if not readiness["ready"]:
        return {
            "success": False,
            "contract_type": contract_type,
            "title": None,
            "draft_text": "",
            "clauses": [],
            "readiness": readiness,
            "message": readiness["message"],
        }

    definition = get_contract_definition(contract_type)

    title = definition.title if definition else _format_field_label(contract_type)

    effective_date = _format_effective_date(fields)

    dedicated_clauses = get_clauses_for_contract(contract_type)

    if dedicated_clauses:
        rendered_clauses = get_rendered_clause_blocks(contract_type, fields)
    elif use_fallback:
        rendered_clauses = build_fallback_clause_blocks(contract_type, fields)
    else:
        rendered_clauses = []

    numbered_clause_text = build_numbered_clause_text(rendered_clauses)

    disclaimer_text = ""

    if include_disclaimer:
        disclaimer_text = (
            "\n\nIMPORTANT NOTICE\n\n"
            "This draft is generated for informational and drafting assistance "
            "purposes only. It is not legal advice and does not create a "
            "lawyer-client relationship. Canadian laws may vary by province or "
            "territory, and the parties should consult a qualified legal "
            "professional before signing or relying on this document."
        )

    draft_text = (
        f"{_format_contract_title(title)}\n\n"
        f"Effective Date: {effective_date}\n\n"
        f"{numbered_clause_text}"
        f"{disclaimer_text}"
    ).strip()

    return {
        "success": True,
        "contract_type": contract_type,
        "title": title,
        "effective_date": effective_date,
        "draft_text": draft_text,
        "clauses": rendered_clauses,
        "readiness": readiness,
        "message": "Contract draft generated successfully.",
    }


def generate_contract_draft_text(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
    include_disclaimer: bool = True,
) -> str:
    """
    Convenience function that returns only the final draft text.
    """

    result = generate_contract_draft(
        contract_type=contract_type,
        fields=fields,
        include_disclaimer=include_disclaimer,
    )

    return result.get("draft_text", "")


# ---------------------------------------------------------------------
# Chat-oriented response builder
# ---------------------------------------------------------------------

def build_drafting_chat_response(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a response suitable for your chatbot/API layer.
    """

    result = generate_contract_draft(
        contract_type=contract_type,
        fields=fields,
        include_disclaimer=True,
    )

    if not result["success"]:
        return {
            "reply": result["message"],
            "status": "drafting_failed",
            "contract_type": contract_type,
            "draft": None,
            "readiness": result["readiness"],
        }

    return {
        "reply": result["draft_text"],
        "status": "draft_generated",
        "contract_type": contract_type,
        "draft": result["draft_text"],
        "clauses": result["clauses"],
        "readiness": result["readiness"],
    }


# ---------------------------------------------------------------------
# Utility functions for debugging and tests
# ---------------------------------------------------------------------

def preview_contract_clauses(contract_type: str) -> Dict[str, Any]:
    """
    Return available clause metadata for a contract type.
    Useful for debugging.
    """

    definition = get_contract_definition(contract_type)
    clauses = get_clauses_for_contract(contract_type)

    return {
        "contract_type": contract_type,
        "title": definition.title if definition else None,
        "has_dedicated_clause_library": len(clauses) > 0,
        "clause_count": len(clauses),
        "clauses": [
            {
                "key": clause.key,
                "title": clause.title,
                "required_fields": clause.required_fields,
            }
            for clause in clauses
        ],
    }
