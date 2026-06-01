# app/services/contract_question_generator.py

import json
from app.services.openai_client import call_openai_api
from app.data.contract_schemas import CONTRACT_SCHEMAS

async def generate_next_question_with_openai(
    contract_type: str,
    next_field: str,
    merged_data: dict,
) -> str:
    """
    Generates a user-friendly question for the next missing field using OpenAI.
    """
    if not contract_type or contract_type not in CONTRACT_SCHEMAS:
        return "Please specify the type of contract first."

    schema = CONTRACT_SCHEMAS[contract_type]
    field_display_name = next_field.replace('_', ' ').title() # Simple humanization

    system_prompt = """
You are an AI assistant helping users fill out contract details.
Your goal is to ask one clear and friendly question at a time.
Do not provide legal advice.
Strictly adhere to the requested field.
Do not ask for multiple fields in one question.
All output must be in English.
"""

    user_prompt = f"""
Contract type: {schema.get("display_name", contract_type)}

Known collected data:
{json.dumps(merged_data, ensure_ascii=False, indent=2)}

The next required field to collect is:
"{next_field}" (human-readable: "{field_display_name}")

Please formulate one concise, polite, and professional question in English to ask the user for this specific field.
"""

    try:
        response_content = await call_openai_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini",
            temperature=0.4,
        )
        return response_content
    except Exception as e:
        print(f"Error generating next question: {e}")
        return f"Could you please provide the {field_display_name}?" # Fallback question
