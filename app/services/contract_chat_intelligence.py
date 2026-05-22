# app/services/contract_chat_intelligence.py

import re

from app.services.contract_registry import CONTRACT_TYPES
from app.services.contract_field_rules import get_missing_fields


def detect_contract_type(message: str):

    message = message.lower()

    for contract_type in CONTRACT_TYPES:

        if contract_type.replace("_", " ") in message:
            return contract_type

    if "nda" in message:
        return "nda"

    if "employment" in message:
        return "employment"

    if "lease" in message:
        return "lease_agreement"

    if "loan" in message:
        return "loan_agreement"

    return None


def extract_basic_fields(message: str):

    data = {}

    patterns = {

        "company_name": r"company name is ([a-zA-Z0-9\s]+)",

        "employee_name": r"employee name is ([a-zA-Z\s]+)",

        "salary": r"salary is ([a-zA-Z0-9\s$]+)",

        "job_title": r"position is ([a-zA-Z\s]+)",

        "start_date": r"start date is ([a-zA-Z0-9\s]+)",

        "payment_frequency": r"paid ([a-zA-Z\s]+)"

    }

    message = message.lower()

    for field, pattern in patterns.items():

        match = re.search(pattern, message)

        if match:
            data[field] = match.group(1).strip()

    return data


def analyze_message(contract_type: str, collected_data: dict, message: str):

    extracted = extract_basic_fields(message)

    collected_data.update(extracted)

    missing_fields = get_missing_fields(contract_type, collected_data)

    return {
        "updated_data": collected_data,
        "missing_fields": missing_fields
    }
