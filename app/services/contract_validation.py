# app/services/contract_validation.py

import re
from typing import Any, Dict, List, Tuple, Optional

# اعتبارسنجی‌های پایه برای فیلدهای عمومی
def is_valid_date(value: str) -> bool:
    """Check if date format is reasonable (simple check for YYYY-MM-DD or Month DD, YYYY)."""
    # Simple regex for common date formats
    date_pattern = r'^\d{4}-\d{2}-\d{2}$|^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}$'
    return bool(re.match(date_pattern, value, re.IGNORECASE))

def is_valid_currency(value: str) -> bool:
    """Check if the currency string seems reasonable."""
    # Matches $1,000.00 or 1000.00
    currency_pattern = r'^\$?\d{1,3}(,\d{3})*(\.\d{2})?$'
    return bool(re.match(currency_pattern, value))

def is_valid_email(email: str) -> bool:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_pattern, email))

# لایه اعتبارسنجی اصلی
def validate_contract_fields(contract_type: str, fields: Dict[str, Any]) -> List[str]:
    """
    Validate collected fields based on business rules for Canada.
    Returns a list of error messages. If list is empty, validation passed.
    """
    errors = []

    # 1. Employment Specific Validations
    if contract_type == "employment":
        if "salary" in fields and not is_valid_currency(str(fields["salary"])):
            errors.append("Salary format is invalid. Please use '$' or plain numbers.")
        if "start_date" in fields and not is_valid_date(str(fields["start_date"])):
            errors.append("Start date format is invalid. Use YYYY-MM-DD or Month DD, YYYY.")

    # 2. General Validations
    # Ensure entities (names) are not just numbers
    for key, value in fields.items():
        if "name" in key and isinstance(value, str):
            if len(value.strip()) < 3:
                errors.append(f"The {key.replace('_', ' ')} seems too short.")

    return errors

def check_contract_risk(contract_type: str, fields: Dict[str, Any]) -> List[str]:
    """
    Check for potential legal warnings or high-risk input combinations.
    """
    warnings = []
    
    
    if "salary" in fields and "1000000" in str(fields["salary"]):
        warnings.append("High salary amount detected. Please ensure this is correct for your jurisdiction.")

    return warnings
