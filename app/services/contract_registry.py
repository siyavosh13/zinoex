from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =========================================================
# Data Models
# =========================================================

@dataclass
class FieldDefinition:
    key: str
    label: str
    question: str
    example: Optional[str] = None
    required: bool = True


@dataclass
class ClauseDefinition:
    key: str
    title: str
    text: str
    required_fields: List[str] = field(default_factory=list)
    optional: bool = False


@dataclass
class ContractDefinition:
    key: str
    title: str
    aliases: List[str] = field(default_factory=list)
    required_fields: List[FieldDefinition] = field(default_factory=list)
    optional_fields: List[FieldDefinition] = field(default_factory=list)
    clauses: List[ClauseDefinition] = field(default_factory=list)


# =========================================================
# Common Field Definitions
# =========================================================

COMMON_FIELDS: Dict[str, FieldDefinition] = {
    "party_a": FieldDefinition(
        key="party_a",
        label="Party A",
        question="Who is the first party to the agreement?",
        example="ABC Technologies Inc.",
    ),
    "party_b": FieldDefinition(
        key="party_b",
        label="Party B",
        question="Who is the second party to the agreement?",
        example="XYZ Consulting Ltd.",
    ),
    "effective_date": FieldDefinition(
        key="effective_date",
        label="Effective Date",
        question="What is the effective date of the agreement?",
        example="January 1, 2025",
    ),
    "services": FieldDefinition(
        key="services",
        label="Services",
        question="What services will be provided under the agreement?",
        example="Software development and maintenance services.",
    ),
    "payment_amount": FieldDefinition(
        key="payment_amount",
        label="Payment Amount",
        question="What is the payment amount or fee arrangement?",
        example="$5,000 per month",
    ),
    "governing_law": FieldDefinition(
        key="governing_law",
        label="Governing Law",
        question="Which jurisdiction's laws govern the agreement?",
        example="Ontario, Canada",
        required=False,
    ),
    "term": FieldDefinition(
        key="term",
        label="Term",
        question="What is the duration or term of the agreement?",
        example="12 months",
        required=False,
    ),
    "end_date": FieldDefinition(
        key="end_date",
        label="End Date",
        question="What is the end date of the agreement, if any?",
        example="December 31, 2025",
        required=False,
    ),
    "termination_date": FieldDefinition(
        key="termination_date",
        label="Termination Date",
        question="What is the termination date of the agreement, if any?",
        example="December 31, 2025",
        required=False,
    ),
    "confidential_information": FieldDefinition(
        key="confidential_information",
        label="Confidential Information",
        question="What information is considered confidential?",
        example="Business plans, customer lists, technical specifications.",
    ),
    "employee_title": FieldDefinition(
        key="employee_title",
        label="Employee Title",
        question="What is the employee's job title?",
        example="Software Engineer",
    ),
    "salary": FieldDefinition(
        key="salary",
        label="Salary",
        question="What is the employee's salary or compensation?",
        example="$80,000 per year",
    ),
    "property_address": FieldDefinition(
        key="property_address",
        label="Property Address",
        question="What is the address of the leased property?",
        example="123 Main Street, Toronto, Ontario",
    ),
    "rent_amount": FieldDefinition(
        key="rent_amount",
        label="Rent Amount",
        question="What is the rent amount?",
        example="$2,500 per month",
    ),
    "goods_description": FieldDefinition(
        key="goods_description",
        label="Goods Description",
        question="What goods are being sold?",
        example="100 laptop computers",
    ),
    "purchase_price": FieldDefinition(
        key="purchase_price",
        label="Purchase Price",
        question="What is the purchase price?",
        example="$50,000",
    ),
    "loan_amount": FieldDefinition(
        key="loan_amount",
        label="Loan Amount",
        question="What is the loan amount?",
        example="$100,000",
    ),
    "interest_rate": FieldDefinition(
        key="interest_rate",
        label="Interest Rate",
        question="What is the interest rate?",
        example="5% per annum",
    ),
    "licensed_material": FieldDefinition(
        key="licensed_material",
        label="Licensed Material",
        question="What material or IP is being licensed?",
        example="Proprietary project management software",
    ),
    "license_scope": FieldDefinition(
        key="license_scope",
        label="License Scope",
        question="What is the scope of the license?",
        example="Non-exclusive, non-transferable license for internal business use",
    ),
}


# =========================================================
# Contract Definitions
# =========================================================

CONTRACT_DEFINITIONS: Dict[str, ContractDefinition] = {
    "service_agreement": ContractDefinition(
        key="service_agreement",
        title="Service Agreement",
        aliases=[
            "service agreement",
            "services agreement",
            "service contract",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["services"],
            COMMON_FIELDS["effective_date"],
            COMMON_FIELDS["payment_amount"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["end_date"],
            COMMON_FIELDS["termination_date"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=[
            ClauseDefinition(
                key="services",
                title="Services",
                text=(
                    "The Service Provider shall provide the following services: "
                    "{services_description}."
                ),
                required_fields=["services_description"],
            ),
            ClauseDefinition(
                key="payment",
                title="Payment",
                text=(
                    "In consideration for the services, the Client shall pay "
                    "the Service Provider {fees}."
                ),
                required_fields=["fees"],
            ),
            ClauseDefinition(
                key="term",
                title="Term",
                text=(
                    "This Agreement shall commence on {start_date} and shall "
                    "continue until {end_date}, unless terminated earlier in "
                    "accordance with this Agreement."
                ),
                required_fields=["start_date"],
                optional=True,
            ),
            ClauseDefinition(
                key="governing_law",
                title="Governing Law",
                text=(
                    "This Agreement shall be governed by and construed in "
                    "accordance with {governing_law}."
                ),
                required_fields=["governing_law"],
                optional=True,
            ),
        ],
    ),

    "consulting_agreement": ContractDefinition(
        key="consulting_agreement",
        title="Consulting Agreement",
        aliases=[
            "consulting agreement",
            "consultant agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["services"],
            COMMON_FIELDS["effective_date"],
            COMMON_FIELDS["payment_amount"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["end_date"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "non_disclosure_agreement": ContractDefinition(
        key="non_disclosure_agreement",
        title="Non-Disclosure Agreement",
        aliases=[
            "nda",
            "non disclosure agreement",
            "confidentiality agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["effective_date"],
            COMMON_FIELDS["confidential_information"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "employment_agreement": ContractDefinition(
        key="employment_agreement",
        title="Employment Agreement",
        aliases=[
            "employment contract",
            "employment agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["employee_title"],
            COMMON_FIELDS["salary"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "independent_contractor_agreement": ContractDefinition(
        key="independent_contractor_agreement",
        title="Independent Contractor Agreement",
        aliases=[
            "contractor agreement",
            "independent contractor contract",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["services"],
            COMMON_FIELDS["payment_amount"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "lease_agreement": ContractDefinition(
        key="lease_agreement",
        title="Lease Agreement",
        aliases=[
            "rental agreement",
            "lease contract",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["property_address"],
            COMMON_FIELDS["rent_amount"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["end_date"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "sales_agreement": ContractDefinition(
        key="sales_agreement",
        title="Sales Agreement",
        aliases=[
            "sale agreement",
            "purchase agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["goods_description"],
            COMMON_FIELDS["purchase_price"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "loan_agreement": ContractDefinition(
        key="loan_agreement",
        title="Loan Agreement",
        aliases=[
            "loan contract",
            "lending agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["loan_amount"],
            COMMON_FIELDS["interest_rate"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["governing_law"],
        ],
    ),

    "license_agreement": ContractDefinition(
        key="license_agreement",
        title="License Agreement",
        aliases=[
            "licensing agreement",
            "ip license agreement",
        ],
        required_fields=[
            COMMON_FIELDS["party_a"],
            COMMON_FIELDS["party_b"],
            COMMON_FIELDS["licensed_material"],
            COMMON_FIELDS["license_scope"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["term"],
            COMMON_FIELDS["governing_law"],
        ],
    ),
}


# =========================================================
# Backward Compatibility Aliases
# =========================================================

# بعضی فایل‌های پروژه، مثل contract_chat_intelligence.py،
# از CONTRACT_TYPES استفاده می‌کنند.
# اسم اصلی رجیستری در این فایل CONTRACT_DEFINITIONS است.
# این alias باعث می‌شود import خطا ندهد.
CONTRACT_TYPES = CONTRACT_DEFINITIONS

# اگر جایی از پروژه CONTRACT_REGISTRY را import یا استفاده کند،
# این alias هم برای سازگاری نگه داشته شده.
CONTRACT_REGISTRY = CONTRACT_DEFINITIONS


# =========================================================
# Registry Access Helpers
# =========================================================

def _normalize_text(value: str) -> str:
    """
    Normalize text for matching contract keys and aliases.
    """
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def normalize_contract_type(contract_type: Optional[str]) -> str:
    """
    Normalize a contract type.

    Examples:
    - "service agreement" -> "service_agreement"
    - "service-agreement" -> "service_agreement"
    - "NDA" -> "non_disclosure_agreement"
    """
    if not contract_type:
        return ""

    clean = _normalize_text(contract_type)

    registry = _get_registry()

    if clean in registry:
        return clean

    for key, definition in registry.items():
        aliases = [_normalize_text(alias) for alias in definition.aliases]

        if clean in aliases:
            return key

    return clean


def _get_registry() -> Dict[str, ContractDefinition]:
    """
    Return the active contract registry.

    Supports:
    - CONTRACT_TYPES
    - CONTRACT_REGISTRY
    - CONTRACT_DEFINITIONS
    """
    if "CONTRACT_TYPES" in globals():
        return globals()["CONTRACT_TYPES"]

    if "CONTRACT_REGISTRY" in globals():
        return globals()["CONTRACT_REGISTRY"]

    if "CONTRACT_DEFINITIONS" in globals():
        return globals()["CONTRACT_DEFINITIONS"]

    return {}


def get_contract_definition(contract_type: Optional[str]) -> Optional[ContractDefinition]:
    """
    Return contract definition by contract type.

    Supports exact keys and aliases.
    """
    if not contract_type:
        return None

    registry = _get_registry()
    normalized = normalize_contract_type(contract_type)

    return registry.get(normalized)


def is_supported_contract_type(contract_type: Optional[str]) -> bool:
    """
    Check whether a contract type is supported.

    Supports exact keys and aliases.
    """
    if not contract_type:
        return False

    registry = _get_registry()
    normalized = normalize_contract_type(contract_type)

    return normalized in registry


def get_required_fields(contract_type: Optional[str]) -> List[FieldDefinition]:
    """
    Return required fields for a contract type.
    """
    definition = get_contract_definition(contract_type)

    if not definition:
        return []

    return list(definition.required_fields or [])


def get_optional_fields(contract_type: Optional[str]) -> List[FieldDefinition]:
    """
    Return optional fields for a contract type.
    """
    definition = get_contract_definition(contract_type)

    if not definition:
        return []

    return list(definition.optional_fields or [])


def get_all_fields(contract_type: Optional[str]) -> List[FieldDefinition]:
    """
    Return required + optional fields for a contract type.
    """
    return get_required_fields(contract_type) + get_optional_fields(contract_type)


def get_supported_contract_types() -> List[str]:
    """
    Return all supported contract type keys.
    """
    registry = _get_registry()
    return sorted(registry.keys())


def list_supported_contract_types() -> List[str]:
    """
    Return all supported contract type keys.

    Kept for compatibility with older code.
    """
    return get_supported_contract_types()


def list_supported_contracts() -> List[ContractDefinition]:
    """
    Return all supported contract definitions.
    """
    registry = _get_registry()
    return list(registry.values())
