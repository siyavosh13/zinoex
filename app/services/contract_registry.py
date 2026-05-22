# app/services/contract_registry.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FieldDefinition:
    """
    Defines a data field required or optionally used in a contract.
    """
    key: str
    label: str
    question: str
    field_type: str = "text"
    required: bool = True
    example: Optional[str] = None
    help_text: Optional[str] = None


@dataclass(frozen=True)
class ClauseDefinition:
    """
    Defines a clause that should appear in a contract.
    """
    key: str
    title: str
    mandatory: bool = True
    order: int = 100
    description: Optional[str] = None


@dataclass(frozen=True)
class ContractDefinition:
    """
    Defines the structure and metadata of a contract type.
    """
    key: str
    title: str
    description: str
    category: str
    risk_level: str
    required_fields: List[FieldDefinition] = field(default_factory=list)
    optional_fields: List[FieldDefinition] = field(default_factory=list)
    clauses: List[ClauseDefinition] = field(default_factory=list)


# ---------------------------------------------------------------------
# Common reusable field definitions
# ---------------------------------------------------------------------

COMMON_FIELDS = {
    "party_1_name": FieldDefinition(
        key="party_1_name",
        label="First Party Legal Name",
        question="What is the full legal name of the first party?",
        example="ABC Technologies Ltd."
    ),
    "party_2_name": FieldDefinition(
        key="party_2_name",
        label="Second Party Legal Name",
        question="What is the full legal name of the second party?",
        example="John Smith"
    ),
    "effective_date": FieldDefinition(
        key="effective_date",
        label="Effective Date",
        question="What is the effective date of the agreement?",
        field_type="date",
        example="March 1, 2025"
    ),
    "governing_law": FieldDefinition(
        key="governing_law",
        label="Governing Law",
        question="Which jurisdiction's laws should govern this agreement?",
        required=False,
        example="England and Wales"
    ),
    "contract_duration": FieldDefinition(
        key="contract_duration",
        label="Contract Duration",
        question="How long will this agreement remain in effect?",
        required=False,
        example="12 months"
    ),
    "payment_terms": FieldDefinition(
        key="payment_terms",
        label="Payment Terms",
        question="What are the payment terms?",
        required=False,
        example="Monthly payments within 15 days of invoice"
    ),
    "termination_notice": FieldDefinition(
        key="termination_notice",
        label="Termination Notice",
        question="How much notice is required to terminate the agreement?",
        required=False,
        example="30 days written notice"
    ),
}


# ---------------------------------------------------------------------
# Common reusable clause definitions
# ---------------------------------------------------------------------

COMMON_CLAUSES = {
    "introduction": ClauseDefinition(
        key="introduction",
        title="Introduction",
        mandatory=True,
        order=1
    ),
    "definitions": ClauseDefinition(
        key="definitions",
        title="Definitions",
        mandatory=True,
        order=2
    ),
    "term": ClauseDefinition(
        key="term",
        title="Term",
        mandatory=True,
        order=10
    ),
    "fees_and_payment": ClauseDefinition(
        key="fees_and_payment",
        title="Fees and Payment",
        mandatory=False,
        order=20
    ),
    "confidentiality": ClauseDefinition(
        key="confidentiality",
        title="Confidentiality",
        mandatory=False,
        order=40
    ),
    "intellectual_property": ClauseDefinition(
        key="intellectual_property",
        title="Intellectual Property",
        mandatory=False,
        order=50
    ),
    "representations": ClauseDefinition(
        key="representations",
        title="Representations and Warranties",
        mandatory=False,
        order=60
    ),
    "limitation_of_liability": ClauseDefinition(
        key="limitation_of_liability",
        title="Limitation of Liability",
        mandatory=False,
        order=70
    ),
    "indemnity": ClauseDefinition(
        key="indemnity",
        title="Indemnification",
        mandatory=False,
        order=80
    ),
    "termination": ClauseDefinition(
        key="termination",
        title="Termination",
        mandatory=True,
        order=90
    ),
    "governing_law": ClauseDefinition(
        key="governing_law",
        title="Governing Law",
        mandatory=True,
        order=100
    ),
    "dispute_resolution": ClauseDefinition(
        key="dispute_resolution",
        title="Dispute Resolution",
        mandatory=True,
        order=110
    ),
    "notices": ClauseDefinition(
        key="notices",
        title="Notices",
        mandatory=False,
        order=120
    ),
    "entire_agreement": ClauseDefinition(
        key="entire_agreement",
        title="Entire Agreement",
        mandatory=True,
        order=130
    ),
    "signatures": ClauseDefinition(
        key="signatures",
        title="Signatures",
        mandatory=True,
        order=999
    ),
}


def clauses(*keys: str) -> List[ClauseDefinition]:
    """
    Helper to build clause lists in a clean way.
    """
    return sorted([COMMON_CLAUSES[key] for key in keys], key=lambda c: c.order)


def fields(*keys: str) -> List[FieldDefinition]:
    """
    Helper to build field lists in a clean way.
    """
    return [COMMON_FIELDS[key] for key in keys]


# ---------------------------------------------------------------------
# Contract-specific field definitions
# ---------------------------------------------------------------------

EMPLOYMENT_FIELDS = {
    "employer_name": FieldDefinition(
        key="employer_name",
        label="Employer Legal Name",
        question="What is the employer's full legal name?",
        example="ABC Technologies Ltd."
    ),
    "employee_name": FieldDefinition(
        key="employee_name",
        label="Employee Full Name",
        question="What is the employee's full legal name?",
        example="John Smith"
    ),
    "job_title": FieldDefinition(
        key="job_title",
        label="Job Title",
        question="What position will the employee hold?",
        example="Software Engineer"
    ),
    "start_date": FieldDefinition(
        key="start_date",
        label="Start Date",
        question="What is the employee's start date?",
        field_type="date",
        example="March 1, 2025"
    ),
    "salary": FieldDefinition(
        key="salary",
        label="Salary",
        question="What is the employee's salary or compensation?",
        example="$80,000 per year"
    ),
    "work_location": FieldDefinition(
        key="work_location",
        label="Work Location",
        question="Where will the employee primarily work?",
        required=False,
        example="London office / Remote"
    ),
    "probation_period": FieldDefinition(
        key="probation_period",
        label="Probation Period",
        question="Is there a probation period?",
        required=False,
        example="3 months"
    ),
}

NDA_FIELDS = {
    "disclosing_party": FieldDefinition(
        key="disclosing_party",
        label="Disclosing Party",
        question="Who is the disclosing party?",
        example="ABC Technologies Ltd."
    ),
    "receiving_party": FieldDefinition(
        key="receiving_party",
        label="Receiving Party",
        question="Who is the receiving party?",
        example="XYZ Capital Ltd."
    ),
    "purpose": FieldDefinition(
        key="purpose",
        label="Purpose of Disclosure",
        question="What is the purpose of sharing confidential information?",
        example="Evaluation of a potential investment"
    ),
    "confidentiality_period": FieldDefinition(
        key="confidentiality_period",
        label="Confidentiality Period",
        question="How long should confidentiality obligations last?",
        example="3 years"
    ),
}

SERVICE_FIELDS = {
    "client_name": FieldDefinition(
        key="client_name",
        label="Client Legal Name",
        question="What is the client's full legal name?",
        example="ABC Ltd."
    ),
    "provider_name": FieldDefinition(
        key="provider_name",
        label="Service Provider Legal Name",
        question="What is the service provider's full legal name?",
        example="Digital Solutions Inc."
    ),
    "services_description": FieldDefinition(
        key="services_description",
        label="Services Description",
        question="What services will be provided?",
        example="Website design and maintenance services"
    ),
    "fees": FieldDefinition(
        key="fees",
        label="Fees",
        question="What are the fees for the services?",
        example="$5,000 fixed fee"
    ),
}

LEASE_FIELDS = {
    "landlord_name": FieldDefinition(
        key="landlord_name",
        label="Landlord Name",
        question="What is the landlord's full legal name?",
        example="Property Holdings Ltd."
    ),
    "tenant_name": FieldDefinition(
        key="tenant_name",
        label="Tenant Name",
        question="What is the tenant's full legal name?",
        example="John Smith"
    ),
    "property_address": FieldDefinition(
        key="property_address",
        label="Property Address",
        question="What is the address of the property?",
        example="10 Baker Street, London"
    ),
    "rent_amount": FieldDefinition(
        key="rent_amount",
        label="Rent Amount",
        question="What is the rent amount?",
        example="$2,000 per month"
    ),
    "lease_term": FieldDefinition(
        key="lease_term",
        label="Lease Term",
        question="What is the lease term?",
        example="12 months"
    ),
}

LOAN_FIELDS = {
    "lender_name": FieldDefinition(
        key="lender_name",
        label="Lender Name",
        question="Who is the lender?",
        example="ABC Finance Ltd."
    ),
    "borrower_name": FieldDefinition(
        key="borrower_name",
        label="Borrower Name",
        question="Who is the borrower?",
        example="John Smith"
    ),
    "loan_amount": FieldDefinition(
        key="loan_amount",
        label="Loan Amount",
        question="What is the loan amount?",
        example="$50,000"
    ),
    "interest_rate": FieldDefinition(
        key="interest_rate",
        label="Interest Rate",
        question="What is the interest rate?",
        example="5% per year"
    ),
    "repayment_terms": FieldDefinition(
        key="repayment_terms",
        label="Repayment Terms",
        question="What are the repayment terms?",
        example="Monthly installments over 24 months"
    ),
}


# ---------------------------------------------------------------------
# Contract Registry: 20 contract types
# ---------------------------------------------------------------------

CONTRACT_DEFINITIONS: Dict[str, ContractDefinition] = {
    "employment": ContractDefinition(
        key="employment",
        title="Employment Agreement",
        description="Agreement between an employer and an employee.",
        category="Employment",
        risk_level="high",
        required_fields=[
            EMPLOYMENT_FIELDS["employer_name"],
            EMPLOYMENT_FIELDS["employee_name"],
            EMPLOYMENT_FIELDS["job_title"],
            EMPLOYMENT_FIELDS["start_date"],
            EMPLOYMENT_FIELDS["salary"],
        ],
        optional_fields=[
            EMPLOYMENT_FIELDS["work_location"],
            EMPLOYMENT_FIELDS["probation_period"],
            COMMON_FIELDS["governing_law"],
            COMMON_FIELDS["termination_notice"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "nda": ContractDefinition(
        key="nda",
        title="Non-Disclosure Agreement",
        description="Agreement protecting confidential information.",
        category="Confidentiality",
        risk_level="medium",
        required_fields=[
            NDA_FIELDS["disclosing_party"],
            NDA_FIELDS["receiving_party"],
            NDA_FIELDS["purpose"],
            NDA_FIELDS["confidentiality_period"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "confidentiality",
            "term",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "service_agreement": ContractDefinition(
        key="service_agreement",
        title="Service Agreement",
        description="Agreement for the provision of services.",
        category="Commercial",
        risk_level="medium",
        required_fields=[
            SERVICE_FIELDS["client_name"],
            SERVICE_FIELDS["provider_name"],
            SERVICE_FIELDS["services_description"],
            SERVICE_FIELDS["fees"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["contract_duration"],
            COMMON_FIELDS["termination_notice"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "representations",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "freelance": ContractDefinition(
        key="freelance",
        title="Freelance Contractor Agreement",
        description="Agreement between a client and an independent freelancer.",
        category="Commercial",
        risk_level="medium",
        required_fields=[
            SERVICE_FIELDS["client_name"],
            SERVICE_FIELDS["provider_name"],
            SERVICE_FIELDS["services_description"],
            SERVICE_FIELDS["fees"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["termination_notice"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "lease": ContractDefinition(
        key="lease",
        title="Lease Agreement",
        description="Agreement for leasing residential or commercial property.",
        category="Real Estate",
        risk_level="high",
        required_fields=[
            LEASE_FIELDS["landlord_name"],
            LEASE_FIELDS["tenant_name"],
            LEASE_FIELDS["property_address"],
            LEASE_FIELDS["rent_amount"],
            LEASE_FIELDS["lease_term"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["governing_law"],
            COMMON_FIELDS["termination_notice"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "loan": ContractDefinition(
        key="loan",
        title="Loan Agreement",
        description="Agreement documenting a loan and repayment obligations.",
        category="Finance",
        risk_level="high",
        required_fields=[
            LOAN_FIELDS["lender_name"],
            LOAN_FIELDS["borrower_name"],
            LOAN_FIELDS["loan_amount"],
            LOAN_FIELDS["interest_rate"],
            LOAN_FIELDS["repayment_terms"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "fees_and_payment",
            "representations",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "partnership": ContractDefinition(
        key="partnership",
        title="Partnership Agreement",
        description="Agreement between business partners.",
        category="Corporate",
        risk_level="high",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="business_purpose",
                label="Business Purpose",
                question="What is the purpose of the partnership?",
                required=False,
                example="Operating an online retail business"
            ),
            FieldDefinition(
                key="profit_sharing",
                label="Profit Sharing",
                question="How will profits and losses be shared?",
                required=False,
                example="50/50"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "representations",
            "confidentiality",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "shareholder": ContractDefinition(
        key="shareholder",
        title="Shareholders Agreement",
        description="Agreement governing shareholder rights and obligations.",
        category="Corporate",
        risk_level="high",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="company_name",
                label="Company Name",
                question="What is the name of the company?",
                required=False,
                example="ABC Holdings Ltd."
            ),
            FieldDefinition(
                key="shareholding_details",
                label="Shareholding Details",
                question="What are the shareholding details?",
                required=False,
                example="Party 1 owns 60%, Party 2 owns 40%"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "representations",
            "confidentiality",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "software_development": ContractDefinition(
        key="software_development",
        title="Software Development Agreement",
        description="Agreement for custom software development services.",
        category="Technology",
        risk_level="high",
        required_fields=[
            SERVICE_FIELDS["client_name"],
            SERVICE_FIELDS["provider_name"],
            SERVICE_FIELDS["services_description"],
            SERVICE_FIELDS["fees"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            FieldDefinition(
                key="deliverables",
                label="Deliverables",
                question="What are the software deliverables?",
                required=False,
                example="Web application, admin panel, API integration"
            ),
            FieldDefinition(
                key="milestones",
                label="Milestones",
                question="What are the project milestones?",
                required=False,
                example="Prototype in 30 days, final delivery in 90 days"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "representations",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "licensing": ContractDefinition(
        key="licensing",
        title="License Agreement",
        description="Agreement granting rights to use intellectual property or software.",
        category="Intellectual Property",
        risk_level="high",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="licensed_property",
                label="Licensed Property",
                question="What property or rights are being licensed?",
                required=False,
                example="Software platform, trademark, patent, content library"
            ),
            FieldDefinition(
                key="license_scope",
                label="License Scope",
                question="What is the scope of the license?",
                required=False,
                example="Non-exclusive, worldwide, non-transferable"
            ),
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "distribution": ContractDefinition(
        key="distribution",
        title="Distribution Agreement",
        description="Agreement appointing a distributor for products or services.",
        category="Commercial",
        risk_level="medium",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="territory",
                label="Territory",
                question="What territory does the agreement cover?",
                required=False,
                example="United Kingdom"
            ),
            FieldDefinition(
                key="products",
                label="Products",
                question="What products are being distributed?",
                required=False,
                example="Consumer electronics"
            ),
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "representations",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "reseller": ContractDefinition(
        key="reseller",
        title="Reseller Agreement",
        description="Agreement for resale of products or services.",
        category="Commercial",
        risk_level="medium",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="resold_products",
                label="Products or Services",
                question="What products or services will be resold?",
                required=False,
                example="SaaS subscriptions"
            ),
            FieldDefinition(
                key="commission",
                label="Commission or Margin",
                question="What commission or margin applies?",
                required=False,
                example="20% commission on net sales"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "investment": ContractDefinition(
        key="investment",
        title="Investment Agreement",
        description="Agreement documenting investment terms.",
        category="Finance",
        risk_level="high",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="investment_amount",
                label="Investment Amount",
                question="What is the investment amount?",
                required=False,
                example="$250,000"
            ),
            FieldDefinition(
                key="equity_percentage",
                label="Equity Percentage",
                question="What equity percentage will be issued?",
                required=False,
                example="10%"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "fees_and_payment",
            "representations",
            "confidentiality",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "mou": ContractDefinition(
        key="mou",
        title="Memorandum of Understanding",
        description="Non-binding or partially binding understanding between parties.",
        category="General",
        risk_level="low",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="purpose",
                label="Purpose",
                question="What is the purpose of the MOU?",
                required=False,
                example="Exploring a strategic partnership"
            ),
            COMMON_FIELDS["contract_duration"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "confidentiality",
            "termination",
            "governing_law",
            "entire_agreement",
            "signatures",
        ),
    ),

    "terms_of_service": ContractDefinition(
        key="terms_of_service",
        title="Terms of Service",
        description="Terms governing user access to a platform, website, or app.",
        category="Technology",
        risk_level="high",
        required_fields=[
            FieldDefinition(
                key="company_name",
                label="Company Name",
                question="What is the company or platform operator's legal name?",
                example="ABC Technologies Ltd."
            ),
            FieldDefinition(
                key="service_name",
                label="Service Name",
                question="What is the name of the website, app, or service?",
                example="TaskFlow"
            ),
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            FieldDefinition(
                key="user_rules",
                label="User Rules",
                question="Are there any specific user rules or prohibited activities?",
                required=False,
                example="No scraping, fraud, illegal use, or abuse of the platform"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "intellectual_property",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
        ),
    ),

    "privacy_policy": ContractDefinition(
        key="privacy_policy",
        title="Privacy Policy",
        description="Policy explaining how personal data is collected, used, and protected.",
        category="Technology",
        risk_level="high",
        required_fields=[
            FieldDefinition(
                key="company_name",
                label="Company Name",
                question="What is the company or website operator's legal name?",
                example="ABC Technologies Ltd."
            ),
            FieldDefinition(
                key="website_or_app_name",
                label="Website or App Name",
                question="What is the name of the website or app?",
                example="TaskFlow"
            ),
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            FieldDefinition(
                key="data_collected",
                label="Data Collected",
                question="What categories of personal data are collected?",
                required=False,
                example="Name, email, payment details, usage analytics"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "confidentiality",
            "limitation_of_liability",
            "governing_law",
            "entire_agreement",
        ),
    ),

    "sale_of_goods": ContractDefinition(
        key="sale_of_goods",
        title="Sale of Goods Agreement",
        description="Agreement for the sale and purchase of goods.",
        category="Commercial",
        risk_level="medium",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="goods_description",
                label="Goods Description",
                question="What goods are being sold?",
                required=False,
                example="500 laptop units"
            ),
            FieldDefinition(
                key="purchase_price",
                label="Purchase Price",
                question="What is the purchase price?",
                required=False,
                example="$250,000"
            ),
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "fees_and_payment",
            "representations",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "consulting": ContractDefinition(
        key="consulting",
        title="Consulting Agreement",
        description="Agreement for professional consulting services.",
        category="Commercial",
        risk_level="medium",
        required_fields=[
            SERVICE_FIELDS["client_name"],
            SERVICE_FIELDS["provider_name"],
            SERVICE_FIELDS["services_description"],
            SERVICE_FIELDS["fees"],
            COMMON_FIELDS["effective_date"],
        ],
        optional_fields=[
            COMMON_FIELDS["payment_terms"],
            COMMON_FIELDS["termination_notice"],
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "intellectual_property",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "agency": ContractDefinition(
        key="agency",
        title="Agency Agreement",
        description="Agreement appointing an agent to act on behalf of a principal.",
        category="Commercial",
        risk_level="medium",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="agency_scope",
                label="Agency Scope",
                question="What is the scope of the agent's authority?",
                required=False,
                example="Marketing and introducing customers"
            ),
            FieldDefinition(
                key="commission",
                label="Commission",
                question="What commission will the agent receive?",
                required=False,
                example="10% of net revenue from introduced customers"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "term",
            "fees_and_payment",
            "confidentiality",
            "representations",
            "limitation_of_liability",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),

    "settlement": ContractDefinition(
        key="settlement",
        title="Settlement Agreement",
        description="Agreement resolving a dispute between parties.",
        category="Dispute Resolution",
        risk_level="high",
        required_fields=fields("party_1_name", "party_2_name", "effective_date"),
        optional_fields=[
            FieldDefinition(
                key="settlement_amount",
                label="Settlement Amount",
                question="Is there a settlement payment amount?",
                required=False,
                example="$25,000"
            ),
            FieldDefinition(
                key="dispute_description",
                label="Dispute Description",
                question="Briefly describe the dispute being settled.",
                required=False,
                example="Dispute relating to unpaid invoices"
            ),
            COMMON_FIELDS["governing_law"],
        ],
        clauses=clauses(
            "introduction",
            "definitions",
            "fees_and_payment",
            "confidentiality",
            "representations",
            "termination",
            "governing_law",
            "dispute_resolution",
            "entire_agreement",
            "signatures",
        ),
    ),
}


# ---------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------

def get_contract_definition(contract_type: str) -> Optional[ContractDefinition]:
    """
    Get contract definition by key.
    """
    if not contract_type:
        return None
    return CONTRACT_DEFINITIONS.get(contract_type)


def list_contract_types() -> List[str]:
    """
    Return all supported contract type keys.
    """
    return list(CONTRACT_DEFINITIONS.keys())


def get_contract_title(contract_type: str) -> str:
    """
    Return readable title for contract type.
    """
    definition = get_contract_definition(contract_type)
    return definition.title if definition else "Agreement"


def get_required_fields(contract_type: str) -> List[FieldDefinition]:
    """
    Return required fields for a contract type.
    """
    definition = get_contract_definition(contract_type)
    return definition.required_fields if definition else []


def get_optional_fields(contract_type: str) -> List[FieldDefinition]:
    """
    Return optional fields for a contract type.
    """
    definition = get_contract_definition(contract_type)
    return definition.optional_fields if definition else []


def get_all_fields(contract_type: str) -> List[FieldDefinition]:
    """
    Return required + optional fields for a contract type.
    """
    definition = get_contract_definition(contract_type)
    if not definition:
        return []
    return definition.required_fields + definition.optional_fields


def get_mandatory_clauses(contract_type: str) -> List[ClauseDefinition]:
    """
    Return mandatory clauses for a contract type.
    """
    definition = get_contract_definition(contract_type)
    if not definition:
        return []
    return [clause for clause in definition.clauses if clause.mandatory]


def get_all_clauses(contract_type: str) -> List[ClauseDefinition]:
    """
    Return all clauses for a contract type.
    """
    definition = get_contract_definition(contract_type)
    if not definition:
        return []
    return sorted(definition.clauses, key=lambda c: c.order)


def is_supported_contract_type(contract_type: str) -> bool:
    """
    Check if contract type is supported.
    """
    return contract_type in CONTRACT_DEFINITIONS
