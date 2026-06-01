from typing import Dict, Any, Optional

from app.services.contract_registry import normalize_contract_type


# =========================================================
# Contract Type Mapping
# =========================================================

CLAUSE_LIBRARY_TYPE_ALIASES = {
    "employment_agreement": "employment",
    "non_disclosure_agreement": "nda",
    "independent_contractor_agreement": "freelance",
    "service_agreement": "service_agreement",
    "consulting_agreement": "consulting_agreement",
    "lease_agreement": "lease_agreement",
    "loan_agreement": "loan_agreement",
    "sales_agreement": "sales_agreement",
}


def get_clause_library_contract_type(contract_type: Optional[str]) -> str:
    """
    Converts canonical registry contract type to clause_library contract type.

    Example:
    employment_agreement -> employment
    non_disclosure_agreement -> nda
    """
    canonical = normalize_contract_type(contract_type)

    if not canonical:
        return ""

    return CLAUSE_LIBRARY_TYPE_ALIASES.get(canonical, canonical)


# =========================================================
# Field Mapping
# =========================================================

COMMON_FIELD_ALIASES = {
    # parties
    "party_a": [
        "party_a",
        "employer_name",
        "service_provider_name",
        "client_name",
        "landlord_name",
        "lender_name",
        "seller_name",
        "party_one",
    ],
    "party_b": [
        "party_b",
        "employee_name",
        "freelancer_name",
        "consultant_name",
        "tenant_name",
        "borrower_name",
        "buyer_name",
        "party_two",
    ],

    # dates
    "effective_date": [
        "effective_date",
        "start_date",
    ],
    "end_date": [
        "end_date",
    ],

    # services / work
    "services": [
        "services",
        "services_description",
    ],

    # payment
    "payment_amount": [
        "payment_amount",
        "fees",
    ],

    # employment
    "employee_title": [
        "employee_title",
        "job_title",
    ],
    "salary": [
        "salary",
    ],

    # nda
    "confidential_information": [
        "confidential_information",
    ],
    "term": [
        "term",
        "confidentiality_term",
    ],

    # lease
    "property_address": [
        "property_address",
    ],
    "rent_amount": [
        "rent_amount",
    ],

    # loan
    "loan_amount": [
        "loan_amount",
    ],
    "interest_rate": [
        "interest_rate",
    ],
    "repayment_terms": [
        "repayment_terms",
    ],

    # sales
    "goods_description": [
        "goods_description",
        "item_description",
    ],
    "purchase_price": [
        "purchase_price",
    ],
    "delivery_date": [
        "delivery_date",
    ],

    # common
    "governing_law": [
        "governing_law",
    ],
}


CONTRACT_SPECIFIC_FIELD_ALIASES = {
    "employment_agreement": {
        "party_a": ["employer_name"],
        "party_b": ["employee_name"],
        "employee_title": ["job_title"],
        "effective_date": ["start_date"],
    },
    "non_disclosure_agreement": {
        "party_a": ["party_one"],
        "party_b": ["party_two"],
        "term": ["confidentiality_term"],
    },
    "service_agreement": {
        "party_a": ["service_provider_name"],
        "party_b": ["client_name"],
        "services": ["services_description"],
        "effective_date": ["start_date"],
        "payment_amount": ["payment_amount", "fees"],
    },
    "consulting_agreement": {
        "party_a": ["client_name"],
        "party_b": ["consultant_name"],
        "services": ["services_description"],
        "effective_date": ["start_date"],
    },
    "independent_contractor_agreement": {
        "party_a": ["client_name"],
        "party_b": ["freelancer_name"],
        "services": ["services_description"],
        "effective_date": ["start_date"],
    },
    "lease_agreement": {
        "party_a": ["landlord_name"],
        "party_b": ["tenant_name"],
        "effective_date": ["start_date"],
    },
    "loan_agreement": {
        "party_a": ["lender_name"],
        "party_b": ["borrower_name"],
        "effective_date": ["start_date"],
    },
    "sales_agreement": {
        "party_a": ["seller_name"],
        "party_b": ["buyer_name"],
        "goods_description": ["item_description"],
    },
}


def expand_fields_for_clause_rendering(
    contract_type: Optional[str],
    fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Expands canonical collected fields into all aliases needed by clause templates.

    Example:
    {
        "party_a": "ABC Inc",
        "party_b": "John Smith",
        "employee_title": "Software Engineer",
        "effective_date": "Jan 1, 2025"
    }

    becomes:
    {
        "party_a": "ABC Inc",
        "employer_name": "ABC Inc",
        "party_b": "John Smith",
        "employee_name": "John Smith",
        "employee_title": "Software Engineer",
        "job_title": "Software Engineer",
        "effective_date": "Jan 1, 2025",
        "start_date": "Jan 1, 2025"
    }
    """
    if not isinstance(fields, dict):
        return {}

    canonical_type = normalize_contract_type(contract_type)

    expanded = dict(fields)

    # Apply common aliases
    for canonical_key, aliases in COMMON_FIELD_ALIASES.items():
        value = expanded.get(canonical_key)

        if value is None or value == "":
            continue

        for alias in aliases:
            expanded.setdefault(alias, value)

    # Apply contract-specific aliases
    specific_aliases = CONTRACT_SPECIFIC_FIELD_ALIASES.get(canonical_type, {})

    for canonical_key, aliases in specific_aliases.items():
        value = expanded.get(canonical_key)

        if value is None or value == "":
            continue

        for alias in aliases:
            expanded.setdefault(alias, value)

    return expanded
