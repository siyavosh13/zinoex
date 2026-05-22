import os
import json
import re
from typing import Dict
from openai import AsyncOpenAI

# --- تنظیم کلید امن ---
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=300.0)

# ===================================================================
#              JSON SANITIZER — مهم‌ترین قسمت
# ===================================================================

def extract_json(text: str):
    """
    مدل گاهی چیزهای اضافی می‌نویسد — این تابع فقط JSON واقعی را نگه می‌دارد.
    اگر JSON ناقص باشد، خطا نمی‌دهد و raw_output را برمی‌گرداند.
    """

    if not text:
        return {"overall_score": 0, "summary": "Empty response", "risks": [], "suggestions": []}

    # فقط بین اولین { و آخرین } را استخراج کن
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {
            "overall_score": 0,
            "summary": "No JSON detected",
            "risks": [],
            "suggestions": [],
            "raw_output": text
        }

    json_str = match.group(0)

    # پاکسازی مرسوم
    json_str = (
        json_str
        .replace("\n", "")
        .replace("\t", "")
        .replace("’", "'")
    )

    # تبدیل ' به " فقط اگر باعث خراب نشود
    # یعنی فقط وقتی که کلیدها با ' آمده باشند
    if re.search(r"'[a-zA-Z0-9_ ]+':", json_str):
        json_str = json_str.replace("'", "\"")

    # تلاش برای مقایسه JSON واقعی
    try:
        return json.loads(json_str)
    except Exception as e:
        return {
            "overall_score": 0,
            "summary": f"JSON parsing failed: {str(e)}",
            "risks": [],
            "suggestions": [],
            "raw_output": json_str
        }


# ===================================================================
# Contract Length Helpers
# ===================================================================

def normalize_contract_length(value: str) -> str:
    """
    مقدار انتخاب‌شده توسط کاربر را به short / medium / long تبدیل می‌کند.
    اگر مقدار نامعتبر یا خالی باشد، medium در نظر گرفته می‌شود.
    """

    if not value:
        return "medium"

    value = str(value).strip().lower()

    if value in ["short", "کوتاه"]:
        return "short"

    if value in ["medium", "normal", "standard", "متوسط", "معمولی"]:
        return "medium"

    if value in ["long", "detailed", "full", "بلند", "مفصل", "کامل"]:
        return "long"

    return "medium"


def get_contract_length(answers: Dict) -> str:
    """
    مقدار اندازه قرارداد را از answers استخراج می‌کند.
    هم از کلید مستقیم contract_length پشتیبانی می‌کند،
    هم از متن کامل سؤال داخل فایل contract_questions.json.
    """

    if not answers:
        return "medium"

    possible_keys = [
        "contract_length",
        "Contract length",
        "contract length",
        "How detailed should the generated contract be?",
        "how detailed should the generated contract be?"
    ]

    for key in possible_keys:
        if key in answers and answers.get(key):
            return normalize_contract_length(answers.get(key))

    # حالت امن‌تر: اگر فرانت‌اند متن سؤال را کمی متفاوت فرستاده باشد
    for key, value in answers.items():
        key_text = str(key).strip().lower()
        if "how detailed" in key_text and "contract" in key_text:
            return normalize_contract_length(value)

    return "medium"


def get_contract_length_instruction(contract_length: str) -> str:
    """
    براساس انتخاب کاربر، دستور دقیق برای مدل تولید می‌کند.
    """

    contract_length = normalize_contract_length(contract_length)

    if contract_length == "short":
        return """
Length requirement:
Generate a SHORT contract.
Keep it concise, practical, and easy to read.
Include only the essential legal sections needed for this type of agreement.
Avoid unnecessary repetition, overly long definitions, and excessive legal boilerplate.
The contract should still be complete and usable, but compact.
"""

    if contract_length == "long":
        return """
Length requirement:
Generate a LONG and highly detailed contract.
The contract must be comprehensive, formal, and professionally structured.

Include detailed clauses where relevant, such as:
- Title and introductory paragraph
- Identification of the parties
- Background / recitals if appropriate
- Definitions if useful
- Scope, duties, responsibilities, or services
- Payment, compensation, fees, taxes, and expenses where applicable
- Term, renewal, suspension, and termination
- Confidentiality
- Intellectual property ownership and licenses where applicable
- Data protection, privacy, or security obligations where applicable
- Representations and warranties
- Disclaimers
- Limitation of liability
- Indemnification
- Non-solicitation or non-compete if applicable and requested
- Compliance with laws
- Dispute resolution
- Governing law and jurisdiction
- Notices
- Assignment
- Force majeure
- Severability
- Waiver
- Entire agreement
- Amendments
- Counterparts / electronic signatures if appropriate
- Signature blocks

Use clear section headings and numbered clauses.
Expand each important clause with practical legal detail.
If the user did not provide certain information, use clear placeholders such as [Insert Name], [Insert Date], or [Insert Jurisdiction].
Do not invent sensitive facts that the user did not provide.
"""

    return """
Length requirement:
Generate a MEDIUM-length contract.
The contract should be balanced: more complete than a short template, but not overly lengthy.
Include the standard important sections for this contract type with clear headings and practical legal wording.
Avoid excessive boilerplate, but make sure the agreement is complete, coherent, and ready for review.
If information is missing, use clear placeholders such as [Insert Name], [Insert Date], or [Insert Jurisdiction].
"""


def get_max_output_tokens_by_length(contract_length: str) -> int:
    """
    تعداد توکن خروجی را براساس اندازه قرارداد تنظیم می‌کند.
    """

    contract_length = normalize_contract_length(contract_length)

    if contract_length == "short":
        return 2500

    if contract_length == "long":
        return 8000

    return 4500


# ===================================================================
# Generate Contract
# ===================================================================
async def generate_contract_with_model(
    contract_type: str,
    language: str,
    tone: str,
    context: str,
    answers: Dict,
) -> str:

    contract_length = get_contract_length(answers)
    length_instruction = get_contract_length_instruction(contract_length)
    max_output_tokens = get_max_output_tokens_by_length(contract_length)

    system_prompt = (
        "You are a legal contract drafting assistant. "
        "You must generate clear, legally coherent, complete, and well-structured contracts. "
        "Follow the requested contract length carefully."
    )

    user_prompt = f"""
Contract type: {contract_type}
Language: {language}
Tone: {tone}
Selected contract length: {contract_length}

Context:
{context or "-"}

Answers:
{answers or {}}

{length_instruction}

Drafting instructions:
- Return a full contract in the requested language.
- Use the user's answers as the main source of contract details.
- Do not ignore the selected contract length.
- If important information is missing, use clear placeholders instead of inventing facts.
- Use professional legal formatting with clear headings.
"""

    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_output_tokens=max_output_tokens,
    )

    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    return response.output[0].content[0].text


# ===================================================================
# Review Contract
# ===================================================================
async def review_contract_with_model(text: str, language: str = "fa"):

    contract_text = text[:50000]

    try:
        messages = [
            {"role": "system", "content": "You are an AI contract analyzer. Return ONLY pure JSON."},
            {"role": "user", "content": f"Language: {language}\n\nContract:\n{contract_text}\n\nReturn JSON keys: overall_score, summary, risks, suggestions."}
        ]

        response = await client.responses.create(
            model="gpt-4o-mini",
            input=messages,
            max_output_tokens=4000,
            timeout=300
        )

        # --- استخراج خروجی کامل مدل ---
        if hasattr(response, "output_text") and response.output_text:
            ai_text = response.output_text
        else:
            ai_text = response.output[0].content[0].text

        ai_text = ai_text.strip()

        # --- این قسمت مشکل را 100٪ حل می‌کند ---
        data = extract_json(ai_text)
        return data

    except Exception as e:
        return {
            "overall_score": 0,
            "summary": f"Error: {str(e)}",
            "risks": [],
            "suggestions": []
        }
