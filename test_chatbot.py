import asyncio
import json

from app.services.openai_client import run_contract_chatbot_turn


CONTRACT_SCHEMAS = {
    "nda": {
        "display_name": "Non-Disclosure Agreement",
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

    "employment_agreement": {
        "display_name": "Employment Agreement",
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
            "termination_notice",
            "confidentiality_clause",
            "non_solicitation_clause",
            "contract_length"
        ]
    },

    "service_agreement": {
        "display_name": "Service Agreement",
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

    "general_contract": {
        "display_name": "General Contract",
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


def print_result(result):
    print("\n" + "=" * 80)
    print("BOT REPLY:")
    print(result.get("reply"))
    print("-" * 80)

    print("STATUS:")
    print(result.get("status"))
    print("-" * 80)

    print("DETECTED CONTRACT TYPE:")
    print(result.get("detected_contract_type"))
    print("-" * 80)

    print("MISSING FIELDS:")
    print(json.dumps(result.get("missing_fields"), indent=2, ensure_ascii=False))
    print("-" * 80)

    session = result.get("session", {})
    print("COLLECTED DATA:")
    print(json.dumps(session.get("collected_data", {}), indent=2, ensure_ascii=False))
    print("-" * 80)

    print("SESSION STATE:")
    print(json.dumps({
        "status": session.get("status"),
        "detected_contract_type": session.get("detected_contract_type"),
        "last_requested_fields": session.get("last_requested_fields"),
        "pending_draft_confirmation": session.get("pending_draft_confirmation"),
        "pending_finalization_missing_fields": session.get("pending_finalization_missing_fields"),
        "last_missing_prompt": session.get("last_missing_prompt"),
    }, indent=2, ensure_ascii=False))
    print("=" * 80)

    if result.get("draft"):
        print("\n" + "#" * 80)
        print("DRAFT GENERATED:")
        print("#" * 80)
        print(result.get("draft")[:5000])

        if len(result.get("draft")) > 5000:
            print("\n--- Draft output truncated in test display ---")


async def run_scripted_test(test_name, messages):
    print("\n\n")
    print("#" * 100)
    print(f"RUNNING TEST: {test_name}")
    print("#" * 100)

    session = {}

    for index, message in enumerate(messages, start=1):
        print("\n\n")
        print(f"USER MESSAGE #{index}:")
        print(message)

        result = await run_contract_chatbot_turn(
            user_message=message,
            session=session,
            contract_schemas=CONTRACT_SCHEMAS,
            language="en",
            tone="professional",
            context="This contract is intended for use in Canada unless a specific province is provided."
        )

        session = result.get("session", {})
        print_result(result)

        if result.get("draft"):
            print("\nDraft generated. Ending this scripted test.")
            break


async def test_nda_complete_flow():
    messages = [
        "I need an NDA for my startup.",
        "The disclosing party is MapleTech Inc.",
        "The receiving party is John Smith.",
        "The effective date is June 1, 2026.",
        "The confidential information includes source code, business plans, customer lists, financial records, and investor materials.",
        "The purpose is to evaluate a possible investment.",
        "The term should be 3 years.",
        "The governing law is Ontario, Canada.",
        "Generate the draft."
    ]

    await run_scripted_test("NDA - Complete Flow", messages)


async def test_nda_multi_field_flow():
    messages = [
        "I need a non-disclosure agreement.",
        "The disclosing party is MapleTech Inc. and the receiving party is John Smith.",
        "Effective date is June 1, 2026. The purpose is evaluating a possible investment.",
        "Confidential information includes source code, customer data, business plans, and financial information.",
        "The term is 3 years and the governing law is Ontario, Canada.",
        "Make it medium length.",
        "Generate it."
    ]

    await run_scripted_test("NDA - Multiple Fields In One Message", messages)


async def test_employment_complete_flow():
    messages = [
        "I need an employment agreement.",
        "The employer is NorthPeak Solutions Ltd. and the employee is Sarah Johnson.",
        "She will work as a Marketing Manager starting July 1, 2026.",
        "The work location is Toronto, Ontario.",
        "The salary is CAD 85,000 per year.",
        "Payment frequency is bi-weekly.",
        "It is full-time employment.",
        "The governing law is Ontario, Canada.",
        "Generate the contract."
    ]

    await run_scripted_test("Employment Agreement - Complete Flow", messages)


async def test_service_agreement_complete_flow():
    messages = [
        "I need a service agreement.",
        "The client is BrightRetail Inc.",
        "The service provider is Nova Digital Studio.",
        "The services are website design, development, testing, and launch support.",
        "The start date is August 1, 2026.",
        "Payment terms are CAD 12,000 total, 50% upfront and 50% upon completion.",
        "The term is 4 months.",
        "The governing law is British Columbia, Canada.",
        "Generate the draft."
    ]

    await run_scripted_test("Service Agreement - Complete Flow", messages)


async def test_missing_fields_confirmation_flow():
    messages = [
        "I need an NDA.",
        "The disclosing party is MapleTech Inc.",
        "The receiving party is John Smith.",
        "Generate the draft.",
        "باشه میگم",
        "The effective date is June 1, 2026.",
        "The confidential information includes product roadmap and investor materials.",
        "The purpose is evaluating a strategic partnership.",
        "The term is 2 years.",
        "The governing law is Ontario, Canada.",
        "Generate it."
    ]

    await run_scripted_test("Missing Fields - User Chooses To Fill Instead", messages)


async def test_generate_with_tbd_flow():
    messages = [
        "I need an NDA.",
        "The disclosing party is MapleTech Inc.",
        "The receiving party is John Smith.",
        "Generate the draft.",
        "Yes, generate it with TBD placeholders."
    ]

    await run_scripted_test("Missing Fields - User Confirms Generate With TBD", messages)


async def interactive_test():
    print("\n")
    print("#" * 100)
    print("INTERACTIVE CHATBOT TEST")
    print("#" * 100)
    print("Type your messages manually.")
    print("Type 'exit' or 'quit' to stop.")
    print("#" * 100)

    session = {}

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() in ["exit", "quit"]:
            print("Stopping interactive test.")
            break

        if not user_message:
            continue

        result = await run_contract_chatbot_turn(
            user_message=user_message,
            session=session,
            contract_schemas=CONTRACT_SCHEMAS,
            language="en",
            tone="professional",
            context="This contract is intended for use in Canada unless a specific province is provided."
        )

        session = result.get("session", {})
        print_result(result)

        if result.get("draft"):
            print("\nDraft has been generated. You can continue testing or type 'exit'.")


async def main():
    """
    Choose which test you want to run.

    For first test, I recommend:
    await test_nda_complete_flow()

    Then test:
    await test_missing_fields_confirmation_flow()
    await test_generate_with_tbd_flow()
    """

    await test_nda_complete_flow()

    # Uncomment these one by one when needed:

    # await test_nda_multi_field_flow()
    # await test_employment_complete_flow()
    # await test_service_agreement_complete_flow()
    # await test_missing_fields_confirmation_flow()
    # await test_generate_with_tbd_flow()

    # For manual chat test, uncomment this:
    # await interactive_test()


if __name__ == "__main__":
    asyncio.run(main())
