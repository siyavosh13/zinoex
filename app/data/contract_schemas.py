# app/data/contract_schemas.py

import json

CONTRACT_SCHEMAS = {
    "nda": {
        "display_name": "Non-Disclosure Agreement",
        "aliases": [
            "nda",
            "non-disclosure agreement",
            "confidentiality agreement",
            "confidential disclosure agreement"
        ],
        "required_fields": [
            "disclosing_party",
            "receiving_party",
            "effective_date",
            "confidential_information_description",
            "purpose",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "mutual_or_one_way",
            "return_or_destroy_information",
            "non_circumvention",
            "remedies",
            "signature_date",
            "contract_length"
        ]
    },

    "mutual_nda": {
        "display_name": "Mutual Non-Disclosure Agreement",
        "aliases": [
            "mutual nda",
            "mutual non-disclosure agreement",
            "two-way nda",
            "bilateral confidentiality agreement"
        ],
        "required_fields": [
            "party_1_name",
            "party_2_name",
            "effective_date",
            "confidential_information_description",
            "purpose",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "return_or_destroy_information",
            "permitted_recipients",
            "remedies",
            "signature_date",
            "contract_length"
        ]
    },

    "employment_agreement": {
        "display_name": "Employment Agreement",
        "aliases": [
            "employment agreement",
            "employment contract",
            "job contract",
            "employee agreement"
        ],
        "required_fields": [
            "employer_name",
            "employee_name",
            "job_title",
            "start_date",
            "work_location",
            "salary_or_wage",
            "payment_frequency",
            "employment_type",
            "governing_law"
        ],
        "optional_fields": [
            "probation_period",
            "benefits",
            "vacation",
            "bonus_or_commission",
            "termination_notice",
            "confidentiality_clause",
            "non_solicitation_clause",
            "intellectual_property_clause",
            "contract_length"
        ]
    },

    "independent_contractor_agreement": {
        "display_name": "Independent Contractor Agreement",
        "aliases": [
            "independent contractor agreement",
            "contractor agreement",
            "freelancer agreement",
            "freelance contract"
        ],
        "required_fields": [
            "client_name",
            "contractor_name",
            "services_description",
            "start_date",
            "payment_terms",
            "contractor_status",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "deliverables",
            "expenses",
            "intellectual_property",
            "confidentiality",
            "non_solicitation",
            "termination_clause",
            "limitation_of_liability",
            "contract_length"
        ]
    },

    "consulting_agreement": {
        "display_name": "Consulting Agreement",
        "aliases": [
            "consulting agreement",
            "consultant agreement",
            "business consulting contract"
        ],
        "required_fields": [
            "client_name",
            "consultant_name",
            "consulting_services",
            "start_date",
            "payment_terms",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "deliverables",
            "expenses",
            "confidentiality",
            "intellectual_property",
            "termination_clause",
            "liability_limit",
            "contract_length"
        ]
    },

    "service_agreement": {
        "display_name": "Service Agreement",
        "aliases": [
            "service agreement",
            "services agreement",
            "service contract",
            "client services agreement"
        ],
        "required_fields": [
            "client_name",
            "service_provider_name",
            "services_description",
            "start_date",
            "payment_terms",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "deliverables",
            "expenses",
            "intellectual_property",
            "confidentiality",
            "termination_clause",
            "limitation_of_liability",
            "contract_length"
        ]
    },

    "master_services_agreement": {
        "display_name": "Master Services Agreement",
        "aliases": [
            "master services agreement",
            "msa",
            "master service agreement"
        ],
        "required_fields": [
            "client_name",
            "service_provider_name",
            "scope_framework",
            "payment_terms",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "statements_of_work",
            "change_orders",
            "service_levels",
            "confidentiality",
            "intellectual_property",
            "limitation_of_liability",
            "indemnity",
            "termination_clause",
            "contract_length"
        ]
    },

    "statement_of_work": {
        "display_name": "Statement of Work",
        "aliases": [
            "statement of work",
            "sow",
            "project statement of work"
        ],
        "required_fields": [
            "client_name",
            "service_provider_name",
            "project_description",
            "deliverables",
            "timeline",
            "fees",
            "governing_agreement"
        ],
        "optional_fields": [
            "milestones",
            "acceptance_criteria",
            "change_request_process",
            "expenses",
            "assumptions",
            "contract_length"
        ]
    },

    "sales_agreement": {
        "display_name": "Sales Agreement",
        "aliases": [
            "sales agreement",
            "sale agreement",
            "goods sale contract",
            "purchase and sale agreement"
        ],
        "required_fields": [
            "seller_name",
            "buyer_name",
            "goods_or_assets",
            "purchase_price",
            "payment_terms",
            "delivery_terms",
            "governing_law"
        ],
        "optional_fields": [
            "inspection_rights",
            "warranties",
            "risk_of_loss",
            "taxes",
            "termination_clause",
            "dispute_resolution",
            "contract_length"
        ]
    },

    "purchase_agreement": {
        "display_name": "Purchase Agreement",
        "aliases": [
            "purchase agreement",
            "asset purchase agreement",
            "business purchase agreement"
        ],
        "required_fields": [
            "buyer_name",
            "seller_name",
            "purchased_assets",
            "purchase_price",
            "closing_date",
            "payment_terms",
            "governing_law"
        ],
        "optional_fields": [
            "representations_and_warranties",
            "conditions_to_closing",
            "excluded_assets",
            "assumed_liabilities",
            "indemnity",
            "confidentiality",
            "contract_length"
        ]
    },

    "loan_agreement": {
        "display_name": "Loan Agreement",
        "aliases": [
            "loan agreement",
            "loan contract",
            "lending agreement"
        ],
        "required_fields": [
            "lender_name",
            "borrower_name",
            "principal_amount",
            "interest_rate",
            "repayment_terms",
            "maturity_date",
            "governing_law"
        ],
        "optional_fields": [
            "security",
            "late_fees",
            "prepayment",
            "default_events",
            "guarantee",
            "contract_length"
        ]
    },

    "promissory_note": {
        "display_name": "Promissory Note",
        "aliases": [
            "promissory note",
            "note payable",
            "simple loan note"
        ],
        "required_fields": [
            "borrower_name",
            "lender_name",
            "principal_amount",
            "interest_rate",
            "repayment_date_or_schedule",
            "governing_law"
        ],
        "optional_fields": [
            "late_payment_fee",
            "prepayment_rights",
            "security",
            "default_terms",
            "contract_length"
        ]
    },

    "commercial_lease_agreement": {
        "display_name": "Commercial Lease Agreement",
        "aliases": [
            "commercial lease",
            "commercial lease agreement",
            "office lease",
            "retail lease"
        ],
        "required_fields": [
            "landlord_name",
            "tenant_name",
            "premises_address",
            "lease_start_date",
            "lease_term",
            "rent_amount",
            "payment_frequency",
            "permitted_use",
            "governing_law"
        ],
        "optional_fields": [
            "security_deposit",
            "operating_costs",
            "utilities",
            "renewal_option",
            "maintenance_responsibilities",
            "insurance_requirements",
            "contract_length"
        ]
    },

    "residential_lease_agreement": {
        "display_name": "Residential Lease Agreement",
        "aliases": [
            "residential lease",
            "rental agreement",
            "tenancy agreement",
            "residential lease agreement"
        ],
        "required_fields": [
            "landlord_name",
            "tenant_name",
            "rental_property_address",
            "lease_start_date",
            "lease_term",
            "rent_amount",
            "payment_frequency",
            "governing_law"
        ],
        "optional_fields": [
            "security_deposit",
            "utilities",
            "pets",
            "parking",
            "occupants",
            "maintenance_responsibilities",
            "contract_length"
        ]
    },

    "partnership_agreement": {
        "display_name": "Partnership Agreement",
        "aliases": [
            "partnership agreement",
            "business partnership agreement"
        ],
        "required_fields": [
            "partner_names",
            "business_name",
            "business_purpose",
            "capital_contributions",
            "profit_and_loss_sharing",
            "management_structure",
            "governing_law"
        ],
        "optional_fields": [
            "decision_making",
            "partner_withdrawal",
            "non_compete",
            "dispute_resolution",
            "dissolution_terms",
            "contract_length"
        ]
    },

    "shareholder_agreement": {
        "display_name": "Shareholder Agreement",
        "aliases": [
            "shareholder agreement",
            "shareholders agreement",
            "corporate shareholder agreement"
        ],
        "required_fields": [
            "corporation_name",
            "shareholder_names",
            "share_structure",
            "management_rights",
            "transfer_restrictions",
            "governing_law"
        ],
        "optional_fields": [
            "right_of_first_refusal",
            "shotgun_clause",
            "tag_along_rights",
            "drag_along_rights",
            "deadlock_resolution",
            "confidentiality",
            "contract_length"
        ]
    },

    "joint_venture_agreement": {
        "display_name": "Joint Venture Agreement",
        "aliases": [
            "joint venture agreement",
            "jv agreement",
            "joint project agreement"
        ],
        "required_fields": [
            "party_1_name",
            "party_2_name",
            "joint_venture_purpose",
            "contributions",
            "profit_and_loss_sharing",
            "management_structure",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "intellectual_property",
            "confidentiality",
            "deadlock_resolution",
            "exit_rights",
            "non_compete",
            "contract_length"
        ]
    },

    "software_development_agreement": {
        "display_name": "Software Development Agreement",
        "aliases": [
            "software development agreement",
            "software development contract",
            "app development agreement",
            "web development agreement"
        ],
        "required_fields": [
            "client_name",
            "developer_name",
            "software_description",
            "deliverables",
            "timeline",
            "payment_terms",
            "intellectual_property_ownership",
            "governing_law"
        ],
        "optional_fields": [
            "acceptance_testing",
            "maintenance_support",
            "third_party_components",
            "confidentiality",
            "warranties",
            "limitation_of_liability",
            "contract_length"
        ]
    },

    "saas_agreement": {
        "display_name": "SaaS Agreement",
        "aliases": [
            "saas agreement",
            "software as a service agreement",
            "subscription software agreement"
        ],
        "required_fields": [
            "provider_name",
            "customer_name",
            "software_service_description",
            "subscription_fees",
            "subscription_term",
            "permitted_users",
            "governing_law"
        ],
        "optional_fields": [
            "service_levels",
            "support_terms",
            "data_security",
            "privacy_terms",
            "acceptable_use",
            "limitation_of_liability",
            "contract_length"
        ]
    },

    "licensing_agreement": {
        "display_name": "Licensing Agreement",
        "aliases": [
            "licensing agreement",
            "license agreement",
            "ip license agreement",
            "software license agreement"
        ],
        "required_fields": [
            "licensor_name",
            "licensee_name",
            "licensed_property",
            "license_scope",
            "license_fee_or_royalty",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "territory",
            "exclusivity",
            "sublicensing",
            "quality_control",
            "audit_rights",
            "termination_clause",
            "contract_length"
        ]
    },

    "website_terms_of_service": {
        "display_name": "Website Terms of Service",
        "aliases": [
            "terms of service",
            "terms and conditions",
            "website terms",
            "terms of use"
        ],
        "required_fields": [
            "business_name",
            "website_or_app_name",
            "website_url",
            "services_description",
            "user_obligations",
            "governing_law"
        ],
        "optional_fields": [
            "account_registration",
            "payments",
            "refund_policy",
            "intellectual_property",
            "prohibited_uses",
            "limitation_of_liability",
            "termination",
            "contract_length"
        ]
    },

    "privacy_policy": {
        "display_name": "Privacy Policy",
        "aliases": [
            "privacy policy",
            "privacy notice",
            "data privacy policy"
        ],
        "required_fields": [
            "business_name",
            "website_or_app_name",
            "website_url",
            "types_of_personal_information_collected",
            "purposes_of_collection",
            "contact_email",
            "governing_law"
        ],
        "optional_fields": [
            "cookies_or_tracking",
            "third_party_sharing",
            "data_retention",
            "user_rights",
            "international_transfers",
            "security_measures",
            "contract_length"
        ]
    },

    "data_processing_agreement": {
        "display_name": "Data Processing Agreement",
        "aliases": [
            "data processing agreement",
            "dpa",
            "data processing addendum"
        ],
        "required_fields": [
            "controller_name",
            "processor_name",
            "processing_subject_matter",
            "categories_of_personal_data",
            "categories_of_data_subjects",
            "processing_purpose",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "subprocessors",
            "security_measures",
            "audit_rights",
            "breach_notification",
            "data_return_or_deletion",
            "international_transfers",
            "contract_length"
        ]
    },

    "settlement_agreement": {
        "display_name": "Settlement Agreement",
        "aliases": [
            "settlement agreement",
            "settlement contract",
            "dispute settlement agreement"
        ],
        "required_fields": [
            "party_1_name",
            "party_2_name",
            "dispute_description",
            "settlement_amount_or_terms",
            "release_scope",
            "payment_deadline",
            "governing_law"
        ],
        "optional_fields": [
            "confidentiality",
            "non_disparagement",
            "no_admission_of_liability",
            "dismissal_terms",
            "tax_responsibility",
            "contract_length"
        ]
    },

    "release_agreement": {
        "display_name": "Release Agreement",
        "aliases": [
            "release agreement",
            "liability release",
            "waiver and release"
        ],
        "required_fields": [
            "releasor_name",
            "releasee_name",
            "released_claims_description",
            "consideration",
            "effective_date",
            "governing_law"
        ],
        "optional_fields": [
            "mutual_release",
            "confidentiality",
            "no_admission_of_liability",
            "indemnity",
            "contract_length"
        ]
    },

    "termination_agreement": {
        "display_name": "Termination Agreement",
        "aliases": [
            "termination agreement",
            "contract termination agreement",
            "mutual termination agreement"
        ],
        "required_fields": [
            "party_1_name",
            "party_2_name",
            "original_agreement_description",
            "termination_date",
            "remaining_obligations",
            "governing_law"
        ],
        "optional_fields": [
            "final_payment",
            "release",
            "confidentiality",
            "return_of_property",
            "survival_clauses",
            "contract_length"
        ]
    },

    "offer_letter": {
        "display_name": "Offer Letter",
        "aliases": [
            "offer letter",
            "employment offer letter",
            "job offer letter"
        ],
        "required_fields": [
            "employer_name",
            "candidate_name",
            "job_title",
            "start_date",
            "work_location",
            "compensation",
            "employment_type",
            "governing_law"
        ],
        "optional_fields": [
            "benefits",
            "probation_period",
            "reporting_manager",
            "conditions_of_employment",
            "confidentiality",
            "contract_length"
        ]
    },

    "commission_agreement": {
        "display_name": "Commission Agreement",
        "aliases": [
            "commission agreement",
            "sales commission agreement",
            "commission contract"
        ],
        "required_fields": [
            "company_name",
            "representative_name",
            "commissionable_activities",
            "commission_rate",
            "payment_schedule",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "territory",
            "quota",
            "chargebacks",
            "expenses",
            "termination_clause",
            "contract_length"
        ]
    },

    "distribution_agreement": {
        "display_name": "Distribution Agreement",
        "aliases": [
            "distribution agreement",
            "distributor agreement",
            "product distribution agreement"
        ],
        "required_fields": [
            "supplier_name",
            "distributor_name",
            "products",
            "territory",
            "pricing_terms",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "exclusivity",
            "minimum_purchase_requirements",
            "marketing_obligations",
            "warranties",
            "termination_clause",
            "contract_length"
        ]
    },

    "reseller_agreement": {
        "display_name": "Reseller Agreement",
        "aliases": [
            "reseller agreement",
            "authorized reseller agreement",
            "channel partner agreement"
        ],
        "required_fields": [
            "vendor_name",
            "reseller_name",
            "products_or_services",
            "territory",
            "resale_terms",
            "payment_terms",
            "governing_law"
        ],
        "optional_fields": [
            "discounts",
            "marketing_rules",
            "customer_support",
            "brand_usage",
            "termination_clause",
            "contract_length"
        ]
    },

    "agency_agreement": {
        "display_name": "Agency Agreement",
        "aliases": [
            "agency agreement",
            "agent agreement",
            "sales agency agreement"
        ],
        "required_fields": [
            "principal_name",
            "agent_name",
            "agency_scope",
            "territory",
            "compensation",
            "term",
            "governing_law"
        ],
        "optional_fields": [
            "exclusivity",
            "authority_limits",
            "reporting_obligations",
            "expenses",
            "termination_clause",
            "contract_length"
        ]
    },

    "general_contract": {
        "display_name": "General Contract",
        "aliases": [
            "general contract",
            "custom agreement",
            "custom contract",
            "other agreement"
        ],
        "required_fields": [
            "contract_type_description",
            "party_1_name",
            "party_2_name",
            "effective_date",
            "main_obligations",
            "payment_terms",
            "term_or_duration",
            "governing_law"
        ],
        "optional_fields": [
            "termination_clause",
            "confidentiality",
            "intellectual_property",
            "liability_limit",
            "dispute_resolution",
            "special_terms",
            "contract_length"
        ]
    }
}


# Helper function to get schema by name
def get_contract_schema(contract_type: str | None):
    if not contract_type:
        return None
    return CONTRACT_SCHEMAS.get(contract_type)

# Helper function to get all valid contract types
def get_valid_contract_types():
    return list(CONTRACT_SCHEMAS.keys())

# Helper function to get human-readable names
def get_contract_display_name(contract_type: str | None):
    schema = get_contract_schema(contract_type)
    return schema.get("display_name", contract_type) if schema else contract_type
