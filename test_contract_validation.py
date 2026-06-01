import json
import traceback


try:
    from app.services.contract_validation import validate_contract_by_type
    from app.services.contract_registry import (
        get_contract_definition,
        normalize_contract_type,
        list_supported_contract_types,
    )
except Exception:
    from contract_validation import validate_contract_by_type
    from contract_registry import (
        get_contract_definition,
        normalize_contract_type,
        list_supported_contract_types,
    )


# Optional imports for drafting layer.
# If these functions do not exist or have different signatures,
# validation tests will still run.
try:
    from app.services.contract_chat_drafting import (
        generate_contract_draft,
        build_drafting_chat_response,
    )
except Exception:
    generate_contract_draft = None
    build_drafting_chat_response = None


def pretty(obj):
    try:
        if hasattr(obj, "to_dict"):
            obj = obj.to_dict()
        elif hasattr(obj, "__dict__"):
            obj = obj.__dict__

        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_validation_case(case):
    print_section(f"VALIDATION CASE: {case['name']}")

    contract_type = case["contract_type"]
    fields = case["fields"]
    expected_success = case["expected_success"]

    print("Input contract_type:", contract_type)
    print("Normalized contract_type:", normalize_contract_type(contract_type))
    print("Input fields:")
    print(pretty(fields))

    result = validate_contract_by_type(contract_type, fields)

    print("\nValidation result:")
    print(pretty(result.to_dict()))

    assert result.success == expected_success, (
        f"{case['name']} failed: expected success={expected_success}, "
        f"got success={result.success}. Errors: {pretty(result.errors)}"
    )

    if expected_success:
        assert result.normalized_fields.get("party_a"), (
            f"{case['name']} failed: party_a was not normalized."
        )
        assert result.normalized_fields.get("party_b"), (
            f"{case['name']} failed: party_b was not normalized."
        )

    print(f"\nPASSED: {case['name']}")


def try_generate_contract_draft(case):
    if generate_contract_draft is None:
        print("\nSkipping generate_contract_draft: function not importable.")
        return

    print_section(f"DRAFT GENERATION CASE: {case['name']}")

    contract_type = case["contract_type"]
    fields = case["fields"]

    try:
        # Most common signature
        draft = generate_contract_draft(contract_type=contract_type, fields=fields)
    except TypeError:
        try:
            # Alternative common signature
            draft = generate_contract_draft(contract_type, fields)
        except Exception as exc:
            print("generate_contract_draft failed with exception:")
            print(type(exc).__name__, str(exc))
            traceback.print_exc()
            return
    except Exception as exc:
        print("generate_contract_draft failed with exception:")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        return

    print("Draft result:")
    print(pretty(draft))


def try_build_drafting_chat_response(case):
    if build_drafting_chat_response is None:
        print("\nSkipping build_drafting_chat_response: function not importable.")
        return

    print_section(f"CHAT RESPONSE CASE: {case['name']}")

    contract_type = case["contract_type"]
    fields = case["fields"]

    try:
        response = build_drafting_chat_response(
            contract_type=contract_type,
            fields=fields,
        )
    except TypeError:
        try:
            response = build_drafting_chat_response(contract_type, fields)
        except Exception as exc:
            print("build_drafting_chat_response failed with exception:")
            print(type(exc).__name__, str(exc))
            traceback.print_exc()
            return
    except Exception as exc:
        print("build_drafting_chat_response failed with exception:")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        return

    print("Chat response result:")
    print(pretty(response))


def test_registry():
    print_section("REGISTRY TEST")

    supported = list_supported_contract_types()
    print("Supported contract types:")
    print(pretty(supported))

    assert "service_agreement" in supported
    assert "non_disclosure_agreement" in supported

    assert normalize_contract_type("nda") == "non_disclosure_agreement"
    assert normalize_contract_type("NDA") == "non_disclosure_agreement"
    assert normalize_contract_type("non-disclosure agreement") == "non_disclosure_agreement"
    assert normalize_contract_type("service agreement") == "service_agreement"

    nda_def = get_contract_definition("nda")
    assert nda_def is not None
    assert nda_def.key == "non_disclosure_agreement"

    service_def = get_contract_definition("service agreement")
    assert service_def is not None
    assert service_def.key == "service_agreement"

    print("PASSED: registry aliases and definitions")


def main():
    test_registry()

    cases = [
        {
            "name": "Valid Service Agreement with legacy names",
            "contract_type": "service_agreement",
            "expected_success": True,
            "fields": {
                "client_name": "Acme Corporation",
                "service_provider_name": "Beta Services LLC",
                "scope_of_services": "Software development and maintenance services",
                "payment_amount": "$10,000",
                "effective_date": "2026-01-01",
                "governing_law": "California",
            },
        },
        {
            "name": "Valid Service Agreement with human type",
            "contract_type": "Service Agreement",
            "expected_success": True,
            "fields": {
                "client_name": "Client Co.",
                "provider_name": "Provider LLC",
                "service_description": "Marketing consulting services",
                "effective_date": "2026-02-01",
            },
        },
        {
            "name": "Valid NDA with short type",
            "contract_type": "nda",
            "expected_success": True,
            "fields": {
                "disclosing_party": "SecretTech Inc.",
                "receiving_party": "Investor Group LLC",
                "effective_date": "2026-03-01",
                "confidential_information": "Financial records and product roadmap",
                "purpose": "Investment evaluation",
            },
        },
        {
            "name": "Valid NDA with snake_case type",
            "contract_type": "non_disclosure_agreement",
            "expected_success": True,
            "fields": {
                "party_a": "Alpha Corp",
                "party_b": "Gamma LLC",
                "effective_date": "2026-04-01",
            },
        },
        {
            "name": "Invalid Service Agreement missing party_b",
            "contract_type": "service_agreement",
            "expected_success": False,
            "fields": {
                "client_name": "Only Client Corp",
                "scope_of_services": "Development services",
                "effective_date": "2026-05-01",
            },
        },
        {
            "name": "Invalid Unsupported Contract Type",
            "contract_type": "unknown_contract",
            "expected_success": False,
            "fields": {
                "party_a": "A",
                "party_b": "B",
                "effective_date": "2026-06-01",
            },
        },
    ]

    for case in cases:
        run_validation_case(case)

    # Optional drafting tests only for successful validation cases
    for case in cases:
        if case["expected_success"]:
            try_generate_contract_draft(case)
            try_build_drafting_chat_response(case)

    print_section("ALL TESTS COMPLETED")
    print("If no assertion failed above, registry + validation normalization are working.")


if __name__ == "__main__":
    main()
