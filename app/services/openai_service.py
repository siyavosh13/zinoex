import os
import json
import httpx
from typing import Dict, Any
from openai import AsyncOpenAI, APITimeoutError, APIConnectionError


async_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=httpx.Timeout(
        connect=30.0,
        read=180.0,
        write=30.0,
        pool=10.0,
    ),
)


# -------------------------------------------------
# Generate Contract
# -------------------------------------------------

async def generate_contract(contract_type: str, details: Dict[str, Any]) -> str:

    try:

        details_text = json.dumps(details, ensure_ascii=False, indent=2)

        prompt = f"""Generate a professional {contract_type} contract.

Details:
{details_text}

Provide a complete legally structured contract with numbered clauses.
"""

        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional legal contract drafting assistant."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        result = response.choices[0].message.content
        return result or ""

    except APITimeoutError:
        raise RuntimeError("Request timeout. Please try again.")

    except APIConnectionError as e:
        raise RuntimeError(f"Connection error: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"Error generating contract: {str(e)}")


# -------------------------------------------------
# Review Contract
# -------------------------------------------------

async def review_contract(contract_text: str) -> Dict[str, Any]:

    try:

        prompt = f"""Analyze the following contract and return a JSON review.

Contract:
{contract_text[:50000]}

Return ONLY valid JSON:

{{
  "overall_score": number 0-100,
  "summary": "short summary",
  "risks": [
    {{
      "title": "",
      "description": "",
      "severity": "high|medium|low"
    }}
  ],
  "suggestions": [
    {{
      "title": "",
      "description": "",
      "priority": "high|medium|low"
    }}
  ]
}}
"""

        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal contract review expert. Respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        raw = response.choices[0].message.content

        if not raw:
            raise ValueError("Empty response")

        raw = raw.strip()

        # حذف markdown اگر مدل اضافه کند
        if raw.startswith("
```"):
raw = "\n".join(raw.split("\n")[1:-1])

try:
result = json.loads(raw)
except json.JSONDecodeError:
return {
"overall_score": 0,
"summary": "AI returned invalid JSON",
"risks": [],
"suggestions": []
}

if not isinstance(result, dict):
result = {}

result.setdefault("overall_score", 0)
result.setdefault("summary", "")
result.setdefault("risks", [])
result.setdefault("suggestions", [])

return result

except APITimeoutError:
return {
"overall_score": 0,
"summary": "Request timeout",
"risks": [],
"suggestions": []
}

except APIConnectionError as e:
return {
"overall_score": 0,
"summary": f"Connection error: {str(e)}",
"risks": [],
"suggestions": []
}

except Exception as e:
return {
"overall_score": 0,
"summary": f"Error: {str(e)}",
"risks": [],
"suggestions": []
}
