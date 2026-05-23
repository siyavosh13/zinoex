import re
from datetime import datetime
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from app.services.contract_clause_library import (
    get_clauses_for_contract,
    render_all_clauses,
)
from app.services.contract_field_rules import (
    get_missing_required_fields,
    normalize_collected_fields,
)
from app.services.contract_registry import (
    get_contract_definition,
    is_supported_contract_type,
    normalize_contract_type,
)
from app.services.contract_validation import validate_contract_by_type


# ---------------------------------------------------------------------
# Basic formatting helpers
# ---------------------------------------------------------------------

def _clean_text(text: str) -> str:
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
    return title.upper().strip()


def _format_effective_date(fields: Dict[str, Any]) -> str:
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
    Supports both the new standardized party fields and older legacy aliases.
    New standard:
        party_a
        party_b
    """

    party_a = fields.get("party_a")
    party_b = fields.get("party_b")

    if party_a and party_b:
        return (
            f'This Agreement is entered into by and between '
            f'{party_a} ("Party A") and {party_b} ("Party B").'
        )

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
                f'This Agreement is entered into by and between '
                f'{left_value} (the "{left_label}") and '
                f'{right_value} (the "{right_label}").'
            )

    return None


def _format_field_label(field_key: str) -> str:
    return str(field_key).replace("_", " ").title()


def _format_governing_law(value: Any) -> str:
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


def _normalize_contract_type(contract_type: Optional[str]) -> str:
    """
    Uses the central registry normalizer.
    This is kept as a local wrapper so older imports/tests do not break.
    """
    if not contract_type:
        return ""

    return normalize_contract_type(contract_type)


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return value.strip() != ""

    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0

    return True


def _is_effectively_empty_placeholder_value(value: Any) -> bool:
    return not _is_non_empty(value)


# ---------------------------------------------------------------------
# Draft field enrichment / template compatibility
# ---------------------------------------------------------------------

def _set_alias_if_missing(target: Dict[str, Any], alias_key: str, source_keys: List[str]) -> None:
    if _is_non_empty(target.get(alias_key)):
        return

    for key in source_keys:
        value = target.get(key)
        if _is_non_empty(value):
            target[alias_key] = value
            return


def enrich_drafting_fields(contract_type: str, fields: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Adds template-compatible aliases to normalized contract fields.

    Validation uses canonical fields like:
        party_a, party_b, services, payment_amount, effective_date

    Some drafting templates still expect names like:
        service_provider_name, client_name, services_description, start_date, fees
    """

    enriched = dict(fields or {})

    # Generic aliases helpful across multiple templates
    _set_alias_if_missing(enriched, "start_date", ["effective_date", "commencement_date", "agreement_date"])
    _set_alias_if_missing(enriched, "effective_date", ["start_date", "commencement_date", "agreement_date"])
    _set_alias_if_missing(enriched, "agreement_date", ["effective_date", "start_date"])
    _set_alias_if_missing(enriched, "services_description", ["services", "scope_of_services", "scope"])
    _set_alias_if_missing(enriched, "fees", ["payment_amount", "fees", "compensation", "price"])
    _set_alias_if_missing(enriched, "payment_amount", ["fees", "compensation", "price"])
    _set_alias_if_missing(enriched, "purpose", ["project_description", "transaction_description", "business_purpose"])

    # Standardized parties
    _set_alias_if_missing(enriched, "service_provider_name", ["party_a"])
    _set_alias_if_missing(enriched, "client_name", ["party_b"])
    _set_alias_if_missing(enriched, "disclosing_party", ["party_a"])
    _set_alias_if_missing(enriched, "receiving_party", ["party_b"])
    _set_alias_if_missing(enriched, "party_one", ["party_a"])
    _set_alias_if_missing(enriched, "party_two", ["party_b"])

    # Contract-specific refinements
    if contract_type == "service_agreement":
        _set_alias_if_missing(enriched, "service_provider_name", ["party_a"])
        _set_alias_if_missing(enriched, "client_name", ["party_b"])
        _set_alias_if_missing(enriched, "services_description", ["services", "scope_of_services", "scope"])
        _set_alias_if_missing(enriched, "start_date", ["effective_date"])
        _set_alias_if_missing(enriched, "fees", ["payment_amount"])
        _set_alias_if_missing(enriched, "payment_terms", ["payment_amount"])

        if not _is_non_empty(enriched.get("end_date")):
            if _is_non_empty(enriched.get("termination_date")):
                enriched["end_date"] = enriched.get("termination_date")

        if not _is_non_empty(enriched.get("termination_date")):
            if _is_non_empty(enriched.get("end_date")):
                enriched["termination_date"] = enriched.get("end_date")

        if not _is_non_empty(enriched.get("governing_law")):
            enriched["governing_law"] = ""

    elif contract_type == "non_disclosure_agreement":
        _set_alias_if_missing(enriched, "disclosing_party", ["party_a"])
        _set_alias_if_missing(enriched, "receiving_party", ["party_b"])
        _set_alias_if_missing(enriched, "start_date", ["effective_date"])

        if not _is_non_empty(enriched.get("governing_law")):
            enriched["governing_law"] = ""

    if contract_type:
        enriched["contract_type"] = contract_type

    return enriched


# ---------------------------------------------------------------------
# Template rendering helpers
# ---------------------------------------------------------------------

def safe_render_template(text: str, fields: Optional[Dict[str, Any]]) -> str:
    """
    Replaces {placeholders} with field values.
    Unknown or empty placeholders remain unchanged so they can be detected later.
    """

    if not text:
        return ""

    context = fields or {}

    def replace(match: re.Match) -> str:
        key = match.group(1).strip()
        value = context.get(key)

        if not _is_non_empty(value):
            return match.group(0)

        return str(value).strip()

    return re.sub(r"\{([^{}]+)\}", replace, text)


def find_unresolved_placeholders(text: str) -> List[str]:
    if not text:
        return []

    return sorted(set(re.findall(r"\{([^{}]+)\}", text)))


def _cleanup_optional_placeholder_artifacts(text: str) -> str:
    """
    Cleans broken English caused by unresolved optional placeholders,
    especially date placeholders in contract clauses.

    Examples fixed:
        continue until {end_date}, unless ...
        continue until , unless ...
        continue until, unless ...
        until .
        until , and
    """

    if not text:
        return ""

    cleaned = text

    # Remove common unresolved placeholder fragments around end/termination dates
    cleaned = re.sub(
        r"\bcontinue\s+until\s+\{(?:end_date|termination_date)\}\s*,?\s*unless\b",
        "continue unless",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\buntil\s+\{(?:end_date|termination_date)\}\s*,?\s*unless\b",
        "unless",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\bcontinue\s+until\s*,\s*unless\b",
        "continue unless",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\bcontinue\s+until\s+unless\b",
        "continue unless",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\buntil\s*,\s*unless\b",
        "unless",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\buntil\s+\.\b",
        ".",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\buntil\s*,\s*and\b",
        "and",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\buntil\s+\{[^{}]+\}",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # If any empty punctuation remains after "until"
    cleaned = re.sub(
        r"\buntil\s*[,.;:]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Normalize punctuation spacing
    cleaned = re.sub(r"\s+,", ",", cleaned)
    cleaned = re.sub(r"\s+\.", ".", cleaned)
    cleaned = re.sub(r",\s*,+", ", ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    return cleaned.strip()


def _render_clause_blocks_with_fields(
    clauses: List[Dict[str, Any]],
    fields: Dict[str, Any],
) -> List[Dict[str, str]]:
    rendered = []

    for clause in clauses or []:
        key = clause.get("key", "") if isinstance(clause, dict) else ""
        title = clause.get("title", "") if isinstance(clause, dict) else ""
        text = clause.get("text", "") if isinstance(clause, dict) else ""

        text = safe_render_template(text, fields)
        text = _cleanup_optional_placeholder_artifacts(text)
        text = _clean_text(text)

        rendered.append(
            {
                "key": key,
                "title": title,
                "text": text,
            }
        )

    return rendered


# ---------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------

def _to_plain_dict(value: Any) -> Any:
    """
    Converts dataclasses / objects / nested lists into JSON/API friendly dicts.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {k: _to_plain_dict(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_to_plain_dict(item) for item in value]

    if isinstance(value, tuple):
        return [_to_plain_dict(item) for item in value]

    if is_dataclass(value):
        return _to_plain_dict(asdict(value))

    if hasattr(value, "__dict__"):
        return _to_plain_dict(vars(value))

    return value


def _validation_to_dict(validation: Any) -> Dict[str, Any]:
    """
    Supports the new ValidationResult dataclass and also dict-style validation
    if your project later changes the implementation.
    """

    if validation is None:
        return {
            "success": False,
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "normalized_contract_type": "",
            "normalized_fields": {},
        }

    if isinstance(validation, dict):
        success = validation.get("success")
        if success is None:
            success = validation.get("is_valid", False)

        normalized_fields = validation.get("normalized_fields") or {}
        normalized_contract_type = validation.get("normalized_contract_type") or (
            normalized_fields.get("contract_type") if isinstance(normalized_fields, dict) else ""
        )

        return {
            **validation,
            "success": bool(success),
            "is_valid": bool(success),
            "errors": _to_plain_dict(validation.get("errors", [])),
            "warnings": _to_plain_dict(validation.get("warnings", [])),
            "normalized_contract_type": normalized_contract_type or "",
            "normalized_fields": normalized_fields,
        }

    success = getattr(validation, "success", None)
    if success is None:
        success = getattr(validation, "is_valid", False)

    errors = getattr(validation, "errors", [])
    warnings = getattr(validation, "warnings", [])
    normalized_contract_type = getattr(validation, "normalized_contract_type", "")
    normalized_fields = getattr(validation, "normalized_fields", {}) or {}

    return {
        "success": bool(success),
        "is_valid": bool(success),
        "errors": _to_plain_dict(errors),
        "warnings": _to_plain_dict(warnings),
        "normalized_contract_type": normalized_contract_type or "",
        "normalized_fields": normalized_fields,
    }


def _append_warning(warnings: List[Dict[str, Any]], warning: Dict[str, Any]) -> None:
    code = warning.get("code")
    field = warning.get("field")

    for item in warnings:
        if item.get("code") == code and item.get("field") == field:
            return

    warnings.append(warning)


def _build_readiness_from_validation(
    contract_type: str,
    validation_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates a readiness object when validation itself fails.
    This prevents the drafting flow from continuing with raw/bad fields.
    """

    errors = validation_result.get("errors", []) or []

    missing_required_fields = []

    for error in errors:
        if not isinstance(error, dict):
            continue

        code = str(error.get("code", "")).lower()
        field = error.get("field") or error.get("key")

        if "missing" in code or code in {"required", "missing_required_field", "required_field_missing"}:
            missing_required_fields.append(
                {
                    "key": field,
                    "label": _format_field_label(field) if field else None,
                    "question": None,
                    "example": None,
                }
            )

    reason = "validation_failed"
    message = "Contract validation failed. Please correct the input fields."

    if missing_required_fields:
        reason = "missing_required_fields"
        message = "Required information is missing."

    normalized_contract_type = (
        validation_result.get("normalized_contract_type")
        or contract_type
        or ""
    )

    if not normalized_contract_type:
        reason = "missing_contract_type"
        message = "Contract type is missing."

    return {
        "ready": False,
        "reason": reason,
        "message": message,
        "missing_required_fields": missing_required_fields,
    }


# ---------------------------------------------------------------------
# Draft validation helpers
# ---------------------------------------------------------------------

def get_drafting_readiness(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Checks whether the draft can be generated.

    Important:
    This function now uses validate_contract_by_type first, so it works with:
        - party_a / party_b
        - legacy party aliases
        - snake_case contract types
        - registry normalized contract types
    """

    raw_fields = normalize_collected_fields(fields)

    normalized_contract_type = _normalize_contract_type(
        contract_type or raw_fields.get("contract_type")
    )

    if not normalized_contract_type:
        return {
            "ready": False,
            "reason": "missing_contract_type",
            "message": "Contract type is missing.",
            "missing_required_fields": [],
        }

    validation = validate_contract_by_type(normalized_contract_type, raw_fields)
    validation_result = _validation_to_dict(validation)

    if not validation_result.get("success", False):
        return _build_readiness_from_validation(
            normalized_contract_type,
            validation_result,
        )

    normalized_fields = validation_result.get("normalized_fields", {}) or {}
    normalized_fields = enrich_drafting_fields(normalized_contract_type, normalized_fields)

    if normalized_fields.get("governing_law"):
        normalized_fields["governing_law"] = _format_governing_law(
            normalized_fields.get("governing_law")
        )

    final_contract_type = (
        validation_result.get("normalized_contract_type")
        or normalized_contract_type
    )

    if not is_supported_contract_type(final_contract_type):
        return {
            "ready": False,
            "reason": "unsupported_contract_type",
            "message": f"Unsupported contract type: {contract_type}",
            "missing_required_fields": [],
        }

    missing_required = get_missing_required_fields(final_contract_type, normalized_fields)

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
    fields = normalize_collected_fields(fields)

    normalized_contract_type = _normalize_contract_type(
        contract_type or fields.get("contract_type")
    )

    fields = enrich_drafting_fields(normalized_contract_type, fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    rendered_clauses = render_all_clauses(normalized_contract_type, fields)
    rendered_clauses = _render_clause_blocks_with_fields(rendered_clauses, fields)

    return rendered_clauses


def build_numbered_clause_text(rendered_clauses: List[Dict[str, str]]) -> str:
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
    fields = normalize_collected_fields(fields)

    normalized_contract_type = _normalize_contract_type(
        contract_type or fields.get("contract_type")
    )

    fields = enrich_drafting_fields(normalized_contract_type, fields)

    if fields.get("governing_law"):
        fields["governing_law"] = _format_governing_law(fields.get("governing_law"))

    definition = get_contract_definition(normalized_contract_type)
    title = definition.title if definition else _format_field_label(normalized_contract_type)

    parties_line = _format_parties_line(fields)
    introduction_text = parties_line or (
        f"This {title} is prepared based on the information provided by the parties."
    )

    purpose_value = (
        fields.get("purpose")
        or fields.get("project_description")
        or fields.get("services_description")
        or fields.get("scope_of_services")
        or fields.get("scope")
        or fields.get("transaction_description")
        or fields.get("business_purpose")
        or "the purpose described by the parties"
    )

    governing_law = _format_governing_law(fields.get("governing_law", "Canada"))

    field_summary_lines = []
    for key, value in fields.items():
        if not _is_non_empty(value):
            continue
        field_summary_lines.append(f"- {_format_field_label(key)}: {value}")

    field_summary = "\n".join(field_summary_lines) if field_summary_lines else (
        "The material commercial terms shall be as agreed by the parties in writing."
    )

    fallback_blocks = [
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

    return _render_clause_blocks_with_fields(fallback_blocks, fields)


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
    Main contract draft generator.

    Flow:
        1. normalize collected fields
        2. normalize contract_type
        3. validate by contract type
        4. use validation.normalized_fields
        5. enrich drafting aliases
        6. render clauses
        7. detect unresolved placeholders
    """

    merged_fields = normalize_collected_fields(fields)

    if contract_type and not merged_fields.get("contract_type"):
        merged_fields["contract_type"] = contract_type

    requested_contract_type = (
        merged_fields.get("contract_type")
        or contract_type
        or ""
    )

    normalized_contract_type = _normalize_contract_type(requested_contract_type)
    merged_fields["contract_type"] = normalized_contract_type

    validation = validate_contract_by_type(
        normalized_contract_type,
        merged_fields,
    )
    validation_result = _validation_to_dict(validation)

    final_contract_type = (
        validation_result.get("normalized_contract_type")
        or normalized_contract_type
        or contract_type
        or ""
    )

    normalized_fields = validation_result.get("normalized_fields", {}) or {}
    normalized_fields = enrich_drafting_fields(final_contract_type, normalized_fields)

    if final_contract_type:
        normalized_fields["contract_type"] = final_contract_type

    if normalized_fields.get("governing_law"):
        normalized_fields["governing_law"] = _format_governing_law(
            normalized_fields.get("governing_law")
        )

    if not validation_result.get("success", False):
        readiness = _build_readiness_from_validation(
            final_contract_type,
            validation_result,
        )

        validation_result["normalized_fields"] = normalized_fields

        return {
            "success": False,
            "contract_type": final_contract_type,
            "title": None,
            "effective_date": None,
            "draft_text": "",
            "clauses": [],
            "readiness": readiness,
            "validation": validation_result,
            "message": readiness.get(
                "message",
                "Contract validation failed. Please correct the input fields.",
            ),
            "normalized_fields": normalized_fields,
        }

    readiness = get_drafting_readiness(final_contract_type, normalized_fields)

    if not readiness["ready"]:
        validation_result["normalized_fields"] = normalized_fields

        return {
            "success": False,
            "contract_type": final_contract_type,
            "title": None,
            "effective_date": None,
            "draft_text": "",
            "clauses": [],
            "readiness": readiness,
            "validation": validation_result,
            "message": readiness["message"],
            "normalized_fields": normalized_fields,
        }

    definition = get_contract_definition(final_contract_type)
    title = definition.title if definition else _format_field_label(final_contract_type)
    effective_date = _format_effective_date(normalized_fields)

    dedicated_clauses = get_clauses_for_contract(final_contract_type)

    if dedicated_clauses:
        rendered_clauses = get_rendered_clause_blocks(
            final_contract_type,
            normalized_fields,
        )
    elif use_fallback:
        rendered_clauses = build_fallback_clause_blocks(
            final_contract_type,
            normalized_fields,
        )
    else:
        rendered_clauses = []

    numbered_clause_text = build_numbered_clause_text(rendered_clauses)

    if not numbered_clause_text:
        numbered_clause_text = (
            "1. General Terms\n\n"
            "The parties agree that the terms of this Agreement shall be interpreted "
            "in accordance with the information provided and any additional written "
            "terms agreed by the parties."
        )

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

    draft_text = safe_render_template(draft_text, normalized_fields)
    draft_text = _cleanup_optional_placeholder_artifacts(draft_text)
    draft_text = _clean_text(draft_text)

    unresolved_placeholders = find_unresolved_placeholders(draft_text)

    warnings = list(validation_result.get("warnings", []) or [])

    if unresolved_placeholders:
        _append_warning(
            warnings,
            {
                "field": "draft_text",
                "message": (
                    "Draft generated, but some template placeholders remain unresolved: "
                    + ", ".join(unresolved_placeholders)
                ),
                "code": "draft_contains_unresolved_placeholders",
                "severity": "warning",
                "placeholders": unresolved_placeholders,
            },
        )

    validation_result["warnings"] = warnings
    validation_result["normalized_fields"] = normalized_fields
    validation_result["normalized_contract_type"] = final_contract_type
    validation_result["success"] = bool(validation_result.get("success", False))
    validation_result["is_valid"] = bool(validation_result.get("success", False))

    return {
        "success": True,
        "contract_type": final_contract_type,
        "title": title,
        "effective_date": effective_date,
        "draft_text": draft_text,
        "clauses": rendered_clauses,
        "readiness": readiness,
        "validation": validation_result,
        "message": "Contract draft generated successfully.",
        "normalized_fields": normalized_fields,
    }


def generate_contract_draft_text(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
    include_disclaimer: bool = True,
) -> str:
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
    result = generate_contract_draft(
        contract_type=contract_type,
        fields=fields,
        include_disclaimer=True,
    )

    final_contract_type = result.get("contract_type", contract_type)

    if not result.get("success", False):
        validation = result.get("validation", {})
        validation_errors = validation.get("errors", [])
        validation_warnings = validation.get("warnings", [])

        return {
            "reply": result.get("message", "Contract drafting failed."),
            "status": "drafting_failed",
            "contract_type": final_contract_type,
            "draft": None,
            "clauses": [],
            "readiness": result.get("readiness", {}),
            "validation": validation,
            "validation_errors": validation_errors,
            "validation_warnings": validation_warnings,
            "normalized_fields": result.get("normalized_fields", {}),
        }

    validation = result.get("validation", {})

    return {
        "reply": result["draft_text"],
        "status": "draft_generated",
        "contract_type": final_contract_type,
        "draft": result["draft_text"],
        "clauses": result["clauses"],
        "readiness": result["readiness"],
        "validation": validation,
        "validation_errors": validation.get("errors", []),
        "validation_warnings": validation.get("warnings", []),
        "normalized_fields": result.get("normalized_fields", {}),
    }


# ---------------------------------------------------------------------
# Utility functions for debugging and tests
# ---------------------------------------------------------------------

def preview_contract_clauses(contract_type: str) -> Dict[str, Any]:
    normalized_contract_type = _normalize_contract_type(contract_type)

    definition = get_contract_definition(normalized_contract_type)
    clauses = get_clauses_for_contract(normalized_contract_type)

    return {
        "contract_type": normalized_contract_type,
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



# ---------------------------------------------------------------------
# Compatibility Class
# ---------------------------------------------------------------------
# Some parts of the project, especially:
# app/routers/contract_chat.py
# import this class:
#
# from app.services.contract_chat_drafting import ContractChatDrafting
#
# This module already provides function-based drafting utilities.
# To avoid changing or removing existing code, this wrapper exposes
# the existing functions as class methods.


class ContractChatDrafting:
    """
    Compatibility wrapper for contract chat drafting functions.

    This class keeps the existing module-level functions intact and exposes
    them through a class-based API for routers/services that expect:

        ContractChatDrafting()
    """

    def __init__(self):
        pass

    def get_drafting_readiness(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return get_drafting_readiness(contract_type, fields)

    def get_rendered_clause_blocks(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        return get_rendered_clause_blocks(contract_type, fields)

    def build_numbered_clause_text(
        self,
        rendered_clauses: List[Dict[str, str]],
    ) -> str:
        return build_numbered_clause_text(rendered_clauses)

    def build_fallback_clause_blocks(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        return build_fallback_clause_blocks(contract_type, fields)

    def generate_contract_draft(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
        include_disclaimer: bool = True,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        return generate_contract_draft(
            contract_type=contract_type,
            fields=fields,
            include_disclaimer=include_disclaimer,
            use_fallback=use_fallback,
        )

    def generate_contract_draft_text(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
        include_disclaimer: bool = True,
    ) -> str:
        return generate_contract_draft_text(
            contract_type=contract_type,
            fields=fields,
            include_disclaimer=include_disclaimer,
        )

    def build_drafting_chat_response(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return build_drafting_chat_response(contract_type, fields)

    def preview_contract_clauses(
        self,
        contract_type: str,
    ) -> Dict[str, Any]:
        return preview_contract_clauses(contract_type)

    # ---------------------------------------------------------
    # Common alias methods for compatibility with router code
    # ---------------------------------------------------------

    def draft(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
        include_disclaimer: bool = True,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Alias for generate_contract_draft.
        """
        return self.generate_contract_draft(
            contract_type=contract_type,
            fields=fields,
            include_disclaimer=include_disclaimer,
            use_fallback=use_fallback,
        )

    def generate(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
        include_disclaimer: bool = True,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Alias for generate_contract_draft.
        """
        return self.generate_contract_draft(
            contract_type=contract_type,
            fields=fields,
            include_disclaimer=include_disclaimer,
            use_fallback=use_fallback,
        )

    def build(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Alias for build_drafting_chat_response.
        """
        return self.build_drafting_chat_response(contract_type, fields)

    def build_chat_response(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Alias for build_drafting_chat_response.
        """
        return self.build_drafting_chat_response(contract_type, fields)

    def create_draft(
        self,
        contract_type: str,
        fields: Optional[Dict[str, Any]],
        include_disclaimer: bool = True,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Alias for generate_contract_draft.
        """
        return self.generate_contract_draft(
            contract_type=contract_type,
            fields=fields,
            include_disclaimer=include_disclaimer,
            use_fallback=use_fallback,
        )
