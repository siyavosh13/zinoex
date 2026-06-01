# app/services/contract_draft_generator.py

import json
from app.services.openai_client import call_openai_api
from app.data.contract_schemas import CONTRACT_SCHEMAS, get_contract_schema

async def generate_contract_draft_with_openai(
    contract_type: str,
    merged_data: dict,
) -> str:
    """
    Generates the final contract draft using OpenAI.
    """
    schema = get_contract_schema(contract_type)
    if not schema:
        raise ValueError(f"Invalid contract type: {contract_type}")

    # Fill missing fields with TBD placeholders in the data sent to the model
    # This ensures the model knows which fields were explicitly left blank by the user
    final_data_for_draft = {}
    all_fields = schema.get("required_fields", []) + schema.get("optional_fields", [])
    for field in all_fields:
        final_data_for_draft[field] = merged_data.get(field, f"[TBD: {field.replace('_', ' ').title()}]")

    system_prompt = """
You are a professional contract drafting assistant.
Your task is to generate a legally sound and well-structured contract in English based on the provided details.

Rules:
- Use clear, professional, and standard legal language.
- Do not invent any party names, contract terms, dates, locations, or governing law unless explicitly provided.
- Use placeholders like "[TBD: Field Name]" for any information that was not provided or explicitly marked as TBD by the user.
- Do not provide legal advice. Your output should be only the contract text.
- Ensure the contract includes standard sections appropriate for the specified contract type.
"""

    user_prompt = f"""
Generate a contract based on the following specifications:

Contract Type: {schema.get("display_name", contract_type)}

Contract Data:
{json.dumps(final_data_for_draft, ensure_ascii=False, indent=2)}

Draft the full contract text.
"""

    try:
        response_content = await call_openai_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o", # Using gpt-4o for potentially higher quality draft
            temperature=0.1, # Lower temperature for factual, less creative output
        )
        return response_content
    except Exception as e:
        print(f"Error generating contract draft: {e}")
        # A fallback could be a generic message or a template-based draft
        return "An error occurred while generating the contract draft. Please try again later."
