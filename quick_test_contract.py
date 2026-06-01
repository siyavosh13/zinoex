from app.services.contract_validation import validate_contract_by_type
from app.services.contract_chat_drafting import generate_contract_draft


def show_result(title, result):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if hasattr(result, "to_dict"):
        print(result.to_dict())
    elif hasattr(result, "__dict__"):
        print(result.__dict__)
    else:
        print(result)


# ---------------------------------------------------------
# Test 1: payment_amount empty should FAIL
# ---------------------------------------------------------
result_1 = validate_contract_by_type(
    "service_agreement",
    {
        "party_a": "ABC Ltd.",
        "party_b": "XYZ Inc.",
        "services": "Software development",
        "effective_date": "2025-01-01",
        "payment_amount": "",
    },
)

show_result("TEST 1 - empty payment_amount should fail", result_1)


# ---------------------------------------------------------
# Test 2: payment_amount filled should PASS
# ---------------------------------------------------------
result_2 = validate_contract_by_type(
    "service_agreement",
    {
        "party_a": "ABC Ltd.",
        "party_b": "XYZ Inc.",
        "services": "Software development",
        "effective_date": "2025-01-01",
        "payment_amount": "$5,000 per month",
    },
)

show_result("TEST 2 - filled payment_amount should pass", result_2)


# ---------------------------------------------------------
# Test 3: draft should not generate broken term text
# ---------------------------------------------------------
draft = generate_contract_draft(
    "service_agreement",
    {
        "party_a": "ABC Ltd.",
        "party_b": "XYZ Inc.",
        "services": "Software development",
        "effective_date": "2025-01-01",
        "payment_amount": "$5,000 per month",
        "end_date": "",
    },
    include_disclaimer=False,
)

show_result("TEST 3 - draft result", draft)


# ---------------------------------------------------------
# Test 4: check bad fragments
# ---------------------------------------------------------
print("\n" + "=" * 80)
print("TEST 4 - bad fragment checks")
print("=" * 80)

text = ""

if isinstance(draft, dict):
    text = draft.get("draft_text", "") or draft.get("text", "") or ""

bad_fragments = [
    "continue until ,",
    "until .",
    "until , unless",
    "{end_date}",
    "{termination_date}",
]

for frag in bad_fragments:
    print(f"{frag}: {frag in text}")

print("\nDraft text preview:")
print(text[:2000])
