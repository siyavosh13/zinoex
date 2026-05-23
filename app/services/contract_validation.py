from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


try:
    from app.services.contract_registry import (
        get_contract_definition,
        normalize_contract_type,
        list_supported_contract_types,
    )
except Exception:
    from contract_registry import (
        get_contract_definition,
        normalize_contract_type,
        list_supported_contract_types,
    )


# =========================================================
# Data Models
# =========================================================

@dataclass
class ValidationIssue:
    field: str
    message: str
    code: str = "validation_error"
    severity: str = "error"


@dataclass
class ValidationResult:
    success: bool
    normalized_contract_type: str
    normalized_fields: Dict[str, Any] = field(default_factory=dict)
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "is_valid": self.is_valid,
            "normalized_contract_type": self.normalized_contract_type,
            "normalized_fields": self.normalized_fields,
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
        }


# =========================================================
# Helpers
# =========================================================

def _is_empty(value: Any) -> bool:
    """
    Returns True when a value should be treated as missing.

    Important for required field validation:
    - None is empty
    - "" is empty
    - "   " is empty
    - [] / {} / () / set() are empty
    - 0 is NOT empty
    - False is NOT empty
    """

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0

    return False


def _clean_key(key: Any) -> str:
    """
    Normalizes input field keys into lower snake_case.

    Examples:
        "Client Name" -> "client_name"
        "client-name" -> "client_name"
        " client_name " -> "client_name"
    """

    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def _copy_first_available(
    fields: Dict[str, Any],
    aliases: List[str],
    target_key: str,
) -> None:
    """
    Copies the first non-empty alias value into target_key
    if target_key is currently empty or missing.

    Does not delete original fields.
    """

    if not _is_empty(fields.get(target_key)):
        return

    for alias in aliases:
        if alias in fields and not _is_empty(fields.get(alias)):
            fields[target_key] = fields[alias]
            return


def _normalize_keys(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes field keys to snake_case/lowercase while keeping values.

    If duplicate normalized keys exist, the first non-empty value wins.
    """

    normalized: Dict[str, Any] = {}

    if not fields:
        return normalized

    for key, value in fields.items():
        clean_key = _clean_key(key)

        if clean_key not in normalized:
            normalized[clean_key] = value
            continue

        if _is_empty(normalized.get(clean_key)) and not _is_empty(value):
            normalized[clean_key] = value

    return normalized


def _normalize_common_field_aliases(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes common aliases into standard registry/template-compatible keys.

    This intentionally keeps original fields and only fills missing equivalents.

    Examples:
        payment_amount -> fees
        fees -> payment_amount

        services -> services_description
        services_description -> services

        effective_date -> start_date
        start_date -> effective_date
    """

    fields = dict(fields or {})

    # -----------------------------------------------------
    # Payment aliases
    # -----------------------------------------------------

    payment_aliases = [
        "payment_amount",
        "amount",
        "compensation",
        "fee",
        "fees",
        "payment",
        "price",
        "contract_value",
        "total_amount",
        "service_fee",
        "service_fees",
    ]

    _copy_first_available(
        fields,
        aliases=payment_aliases,
        target_key="payment_amount",
    )

    _copy_first_available(
        fields,
        aliases=payment_aliases,
        target_key="fees",
    )

    # -----------------------------------------------------
    # Services / scope aliases
    # -----------------------------------------------------

    services_aliases = [
        "services",
        "scope_of_services",
        "service_description",
        "services_description",
        "description_of_services",
        "deliverables",
        "work_scope",
        "scope",
        "statement_of_work",
        "sow",
    ]

    _copy_first_available(
        fields,
        aliases=services_aliases,
        target_key="services",
    )

    _copy_first_available(
        fields,
        aliases=services_aliases,
        target_key="services_description",
    )

    _copy_first_available(
        fields,
        aliases=services_aliases,
        target_key="scope_of_services",
    )

    # -----------------------------------------------------
    # Date aliases
    # -----------------------------------------------------

    date_aliases = [
        "effective_date",
        "start_date",
        "agreement_date",
        "contract_date",
        "commencement_date",
        "execution_date",
    ]

    _copy_first_available(
        fields,
        aliases=date_aliases,
        target_key="effective_date",
    )

    _copy_first_available(
        fields,
        aliases=date_aliases,
        target_key="start_date",
    )

    _copy_first_available(
        fields,
        aliases=date_aliases,
        target_key="agreement_date",
    )

    # -----------------------------------------------------
    # Governing law aliases
    # -----------------------------------------------------

    governing_law_aliases = [
        "governing_law",
        "jurisdiction",
        "applicable_law",
        "law",
        "legal_jurisdiction",
    ]

    _copy_first_available(
        fields,
        aliases=governing_law_aliases,
        target_key="governing_law",
    )

    # -----------------------------------------------------
    # Term aliases
    # -----------------------------------------------------

    term_aliases = [
        "term",
        "duration",
        "contract_term",
        "agreement_term",
        "term_length",
    ]

    _copy_first_available(
        fields,
        aliases=term_aliases,
        target_key="term",
    )

    # -----------------------------------------------------
    # End date / termination date aliases
    # -----------------------------------------------------

    end_date_aliases = [
        "end_date",
        "termination_date",
        "expiry_date",
        "expiration_date",
        "contract_end_date",
    ]

    _copy_first_available(
        fields,
        aliases=end_date_aliases,
        target_key="end_date",
    )

    _copy_first_available(
        fields,
        aliases=end_date_aliases,
        target_key="termination_date",
    )

    return fields


def _normalize_party_aliases(
    contract_type: str,
    fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Converts contract-specific party names to standard party_a / party_b.

    Important:
    - Does not remove old keys.
    - Only fills party_a / party_b if missing.
    - The convention used here must match drafting templates.

    Standard convention:
        party_a = first/main/provider/disclosing/employer side depending on contract
        party_b = second/client/receiving/employee side depending on contract
    """

    fields = dict(fields or {})
    contract_type = normalize_contract_type(contract_type)

    # -----------------------------------------------------
    # General aliases
    # -----------------------------------------------------

    party_a_aliases = [
        "party_a",
        "party_a_name",
        "party_1",
        "party_1_name",
        "party_one",
        "party_one_name",
        "first_party",
        "first_party_name",
    ]

    party_b_aliases = [
        "party_b",
        "party_b_name",
        "party_2",
        "party_2_name",
        "party_two",
        "party_two_name",
        "second_party",
        "second_party_name",
    ]

    # -----------------------------------------------------
    # Contract-specific aliases
    # -----------------------------------------------------

    if contract_type == "service_agreement":
        # Convention:
        # party_a = service provider / vendor
        # party_b = client / customer
        party_a_aliases += [
            "provider",
            "provider_name",
            "service_provider",
            "service_provider_name",
            "vendor",
            "vendor_name",
            "contractor",
            "contractor_name",
        ]

        party_b_aliases += [
            "client",
            "client_name",
            "customer",
            "customer_name",
        ]

    elif contract_type == "consulting_agreement":
        # Convention:
        # party_a = consultant/provider
        # party_b = client/company
        party_a_aliases += [
            "consultant",
            "consultant_name",
            "provider",
            "provider_name",
            "service_provider",
            "service_provider_name",
        ]

        party_b_aliases += [
            "client",
            "client_name",
            "company",
            "company_name",
            "customer",
            "customer_name",
        ]

    elif contract_type == "non_disclosure_agreement":
        # Convention:
        # party_a = disclosing party
        # party_b = receiving party
        party_a_aliases += [
            "disclosing_party",
            "disclosing_party_name",
            "discloser",
            "discloser_name",
            "owner",
            "owner_name",
        ]

        party_b_aliases += [
            "receiving_party",
            "receiving_party_name",
            "recipient",
            "recipient_name",
            "receiver",
            "receiver_name",
        ]

    elif contract_type == "employment_agreement":
        # Convention:
        # party_a = employer/company
        # party_b = employee
        party_a_aliases += [
            "employer",
            "employer_name",
            "company",
            "company_name",
        ]

        party_b_aliases += [
            "employee",
            "employee_name",
            "worker",
            "worker_name",
        ]

    elif contract_type == "independent_contractor_agreement":
        # Convention:
        # party_a = company/client
        # party_b = contractor
        party_a_aliases += [
            "company",
            "company_name",
            "client",
            "client_name",
            "customer",
            "customer_name",
        ]

        party_b_aliases += [
            "contractor",
            "contractor_name",
            "independent_contractor",
            "independent_contractor_name",
        ]

    elif contract_type == "lease_agreement":
        # Convention:
        # party_a = landlord
        # party_b = tenant
        party_a_aliases += [
            "landlord",
            "landlord_name",
            "lessor",
            "lessor_name",
        ]

        party_b_aliases += [
            "tenant",
            "tenant_name",
            "lessee",
            "lessee_name",
        ]

    elif contract_type == "sales_agreement":
        # Convention:
        # party_a = seller
        # party_b = buyer
        party_a_aliases += [
            "seller",
            "seller_name",
            "vendor",
            "vendor_name",
        ]

        party_b_aliases += [
            "buyer",
            "buyer_name",
            "purchaser",
            "purchaser_name",
            "customer",
            "customer_name",
        ]

    elif contract_type == "loan_agreement":
        # Convention:
        # party_a = lender
        # party_b = borrower
        party_a_aliases += [
            "lender",
            "lender_name",
            "creditor",
            "creditor_name",
        ]

        party_b_aliases += [
            "borrower",
            "borrower_name",
            "debtor",
            "debtor_name",
        ]

    elif contract_type == "license_agreement":
        # Convention:
        # party_a = licensor
        # party_b = licensee
        party_a_aliases += [
            "licensor",
            "licensor_name",
            "owner",
            "owner_name",
        ]

        party_b_aliases += [
            "licensee",
            "licensee_name",
            "user",
            "user_name",
        ]

    # -----------------------------------------------------
    # Generic fallback aliases
    # -----------------------------------------------------

    party_a_aliases += [
        "first_named_party",
        "main_party",
        "main_party_name",
    ]

    party_b_aliases += [
        "second_named_party",
        "counterparty",
        "counterparty_name",
    ]

    _copy_first_available(fields, party_a_aliases, "party_a")
    _copy_first_available(fields, party_b_aliases, "party_b")

    return fields


def normalize_contract_fields(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Main field normalization pipeline.

    Steps:
        1. Normalize field keys
        2. Normalize common aliases
        3. Normalize party aliases based on contract type
        4. Normalize common aliases again to catch values introduced by party normalization
    """

    normalized = _normalize_keys(fields or {})
    normalized = _normalize_common_field_aliases(normalized)
    normalized = _normalize_party_aliases(contract_type, normalized)
    normalized = _normalize_common_field_aliases(normalized)

    return normalized


# =========================================================
# Validation
# =========================================================

def validate_required_fields(
    contract_type: str,
    fields: Dict[str, Any],
) -> Tuple[List[ValidationIssue], List[ValidationIssue]]:
    """
    Validates required fields according to the contract registry definition.
    """

    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    normalized_type = normalize_contract_type(contract_type)
    definition = get_contract_definition(normalized_type)

    if not definition:
        supported = ", ".join(list_supported_contract_types())

        errors.append(
            ValidationIssue(
                field="contract_type",
                code="unsupported_contract_type",
                message=(
                    f"Unsupported contract type: {contract_type}. "
                    f"Supported types: {supported}"
                ),
            )
        )

        return errors, warnings

    for field_def in definition.required_fields:
        value = fields.get(field_def.key)

        if _is_empty(value):
            errors.append(
                ValidationIssue(
                    field=field_def.key,
                    code="required_field_missing",
                    message=(
                        f"Required field is missing: "
                        f"{field_def.label} ({field_def.key})"
                    ),
                )
            )

    if _is_empty(fields.get("governing_law")):
        warnings.append(
            ValidationIssue(
                field="governing_law",
                code="recommended_field_missing",
                severity="warning",
                message="Governing law is recommended but not provided.",
            )
        )

    return errors, warnings


def validate_contract_by_type(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> ValidationResult:
    """
    Validates a contract using registry definition and normalized fields.

    Returns:
        ValidationResult
    """

    normalized_type = normalize_contract_type(contract_type)

    normalized_fields = normalize_contract_fields(
        normalized_type,
        fields or {},
    )

    if normalized_type:
        normalized_fields["contract_type"] = normalized_type

    errors, warnings = validate_required_fields(
        normalized_type,
        normalized_fields,
    )

    return ValidationResult(
        success=len(errors) == 0,
        normalized_contract_type=normalized_type,
        normalized_fields=normalized_fields,
        errors=errors,
        warnings=warnings,
    )


def validate_contract_input(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> ValidationResult:
    return validate_contract_by_type(contract_type, fields)


def validate_contract(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> ValidationResult:
    return validate_contract_by_type(contract_type, fields)


def get_validation_error_message(result: ValidationResult) -> str:
    """
    Converts validation errors into a readable message.
    """

    if result.success:
        return ""

    if not result.errors:
        return "Contract validation failed. Please correct the input fields."

    parts = ["Contract validation failed. Please correct the input fields:"]

    for error in result.errors:
        parts.append(f"- {error.field}: {error.message}")

    return "\n".join(parts)


def validate_or_raise(
    contract_type: str,
    fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Useful if drafting code expects exceptions on validation failure.
    Returns normalized fields on success.
    """

    result = validate_contract_by_type(contract_type, fields)

    if not result.success:
        raise ValueError(get_validation_error_message(result))

    return result.normalized_fields
