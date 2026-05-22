from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Clause:
    key: str
    title: str
    template: str
    required_fields: List[str] = field(default_factory=list)

    def render(self, fields: Dict[str, Any]) -> str:
        """
        Render clause template using provided fields.
        If a field is missing, keep the template unchanged for safety.
        """
        try:
            return self.template.format(**fields)
        except KeyError:
            return self.template


CLAUSE_LIBRARY: Dict[str, List[Clause]] = {
    "employment": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Employment Agreement ("Agreement") is made between '
                '{employer_name} ("Employer") and {employee_name} ("Employee"). '
                "The parties agree as follows."
            ),
            required_fields=["employer_name", "employee_name"],
        ),
        Clause(
            key="position_duties",
            title="Position and Duties",
            template=(
                "The Employee shall serve as {job_title} and shall perform "
                "the duties customarily associated with that position, together "
                "with such other duties as may reasonably be assigned by the Employer."
            ),
            required_fields=["job_title"],
        ),
        Clause(
            key="term",
            title="Term",
            template=(
                "The employment shall commence on {start_date} and shall continue "
                "until terminated in accordance with this Agreement."
            ),
            required_fields=["start_date"],
        ),
        Clause(
            key="compensation",
            title="Compensation",
            template=(
                "The Employer shall pay the Employee a salary of {salary}, "
                "subject to applicable deductions, withholdings, and taxes."
            ),
            required_fields=["salary"],
        ),
        Clause(
            key="confidentiality",
            title="Confidentiality",
            template=(
                "The Employee shall not disclose or use any confidential or "
                "proprietary information of the Employer except as required to "
                "perform duties under this Agreement."
            ),
        ),
        Clause(
            key="termination",
            title="Termination",
            template=(
                "Either party may terminate this Agreement in accordance with "
                "applicable law and any notice requirements set forth herein."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by and construed in accordance "
                "with {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "nda": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Non-Disclosure Agreement ("Agreement") is entered into between '
                "{party_one} and {party_two} for the purpose of protecting "
                "confidential information."
            ),
            required_fields=["party_one", "party_two"],
        ),
        Clause(
            key="confidential_information",
            title="Confidential Information",
            template=(
                "Confidential Information means any non-public information disclosed "
                "by either party that is marked confidential or that reasonably should "
                "be understood to be confidential."
            ),
        ),
        Clause(
            key="obligations",
            title="Obligations",
            template=(
                "The receiving party shall not disclose, copy, or use Confidential "
                "Information except for the permitted purpose."
            ),
        ),
        Clause(
            key="term",
            title="Term",
            template=(
                "This Agreement shall remain in effect for {confidentiality_term}."
            ),
            required_fields=["confidentiality_term"],
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "freelance": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Freelance Agreement is made between {client_name} ("Client") '
                'and {freelancer_name} ("Freelancer").'
            ),
            required_fields=["client_name", "freelancer_name"],
        ),
        Clause(
            key="services",
            title="Services",
            template=(
                "The Freelancer shall provide the following services: "
                "{services_description}."
            ),
            required_fields=["services_description"],
        ),
        Clause(
            key="payment",
            title="Payment",
            template=(
                "The Client shall pay the Freelancer {payment_amount} for the Services."
            ),
            required_fields=["payment_amount"],
        ),
        Clause(
            key="timeline",
            title="Timeline",
            template=(
                "The Services shall begin on {start_date} and be completed by {end_date}."
            ),
            required_fields=["start_date", "end_date"],
        ),
        Clause(
            key="independent_contractor",
            title="Independent Contractor",
            template=(
                "The Freelancer is engaged as an independent contractor and not as an employee."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "service_agreement": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Service Agreement ("Agreement") is entered into between '
                '{service_provider_name} ("Service Provider") and {client_name} ("Client").'
            ),
            required_fields=["service_provider_name", "client_name"],
        ),
        Clause(
            key="services",
            title="Services",
            template=(
                "The Service Provider shall perform the following services: "
                "{services_description}."
            ),
            required_fields=["services_description"],
        ),
        Clause(
            key="term",
            title="Term",
            template=(
                "This Agreement shall commence on {start_date} and continue until "
                "{end_date}, unless terminated earlier in accordance with this Agreement."
            ),
            required_fields=["start_date", "end_date"],
        ),
        Clause(
            key="fees",
            title="Fees and Payment",
            template=(
                "In consideration for the services, the Client shall pay "
                "{payment_amount} in accordance with the payment terms agreed by the parties."
            ),
            required_fields=["payment_amount"],
        ),
        Clause(
            key="standard_of_performance",
            title="Standard of Performance",
            template=(
                "The Service Provider shall perform the services in a professional "
                "and workmanlike manner and in accordance with applicable standards."
            ),
        ),
        Clause(
            key="termination",
            title="Termination",
            template=(
                "Either party may terminate this Agreement in accordance with its terms "
                "and upon any required notice."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "consulting_agreement": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Consulting Agreement ("Agreement") is made between '
                '{client_name} ("Client") and {consultant_name} ("Consultant").'
            ),
            required_fields=["client_name", "consultant_name"],
        ),
        Clause(
            key="consulting_services",
            title="Consulting Services",
            template=(
                "The Consultant shall provide the following consulting services: "
                "{services_description}."
            ),
            required_fields=["services_description"],
        ),
        Clause(
            key="term",
            title="Term",
            template=(
                "The consulting engagement shall begin on {start_date} and continue "
                "until {end_date}, unless earlier terminated."
            ),
            required_fields=["start_date", "end_date"],
        ),
        Clause(
            key="compensation",
            title="Compensation",
            template=(
                "The Client shall pay the Consultant {payment_amount} for the services rendered."
            ),
            required_fields=["payment_amount"],
        ),
        Clause(
            key="independent_contractor",
            title="Independent Contractor",
            template=(
                "The Consultant is engaged as an independent contractor and is not "
                "an employee, partner, or agent of the Client except as expressly authorized."
            ),
        ),
        Clause(
            key="confidentiality",
            title="Confidentiality",
            template=(
                "The Consultant shall maintain the confidentiality of all proprietary "
                "and confidential information disclosed by the Client."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "lease_agreement": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Lease Agreement ("Agreement") is made between '
                '{landlord_name} ("Landlord") and {tenant_name} ("Tenant").'
            ),
            required_fields=["landlord_name", "tenant_name"],
        ),
        Clause(
            key="premises",
            title="Premises",
            template=(
                "The Landlord leases to the Tenant the premises located at {property_address}."
            ),
            required_fields=["property_address"],
        ),
        Clause(
            key="term",
            title="Lease Term",
            template=(
                "The lease shall commence on {start_date} and continue until {end_date}."
            ),
            required_fields=["start_date", "end_date"],
        ),
        Clause(
            key="rent",
            title="Rent",
            template=(
                "The Tenant shall pay rent in the amount of {rent_amount} in accordance "
                "with the payment schedule agreed by the parties."
            ),
            required_fields=["rent_amount"],
        ),
        Clause(
            key="use_of_premises",
            title="Use of Premises",
            template=(
                "The Tenant shall use the premises only for lawful purposes and in "
                "accordance with this Agreement."
            ),
        ),
        Clause(
            key="maintenance",
            title="Maintenance and Repairs",
            template=(
                "The parties shall be responsible for maintenance and repairs as set out "
                "in this Agreement and applicable law."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "loan_agreement": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Loan Agreement ("Agreement") is entered into between '
                '{lender_name} ("Lender") and {borrower_name} ("Borrower").'
            ),
            required_fields=["lender_name", "borrower_name"],
        ),
        Clause(
            key="loan_amount",
            title="Loan Amount",
            template=(
                "The Lender agrees to lend the Borrower the principal amount of {loan_amount}."
            ),
            required_fields=["loan_amount"],
        ),
        Clause(
            key="interest",
            title="Interest",
            template=(
                "The outstanding principal shall bear interest at the rate of {interest_rate}."
            ),
            required_fields=["interest_rate"],
        ),
        Clause(
            key="repayment",
            title="Repayment",
            template=(
                "The Borrower shall repay the loan in accordance with the following terms: "
                "{repayment_terms}."
            ),
            required_fields=["repayment_terms"],
        ),
        Clause(
            key="default",
            title="Default",
            template=(
                "Failure by the Borrower to make payments when due shall constitute an "
                "event of default, subject to any applicable cure periods."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],

    "sales_agreement": [
        Clause(
            key="intro",
            title="Introduction",
            template=(
                'This Sales Agreement ("Agreement") is made between '
                '{seller_name} ("Seller") and {buyer_name} ("Buyer").'
            ),
            required_fields=["seller_name", "buyer_name"],
        ),
        Clause(
            key="goods_or_services",
            title="Goods or Services",
            template=(
                "The Seller agrees to sell, and the Buyer agrees to purchase, the following: "
                "{item_description}."
            ),
            required_fields=["item_description"],
        ),
        Clause(
            key="purchase_price",
            title="Purchase Price",
            template=(
                "The total purchase price shall be {purchase_price}."
            ),
            required_fields=["purchase_price"],
        ),
        Clause(
            key="delivery",
            title="Delivery",
            template=(
                "Delivery shall take place on or before {delivery_date} in accordance "
                "with the terms agreed by the parties."
            ),
            required_fields=["delivery_date"],
        ),
        Clause(
            key="risk_of_loss",
            title="Risk of Loss",
            template=(
                "Risk of loss shall pass between the parties as provided in this Agreement."
            ),
        ),
        Clause(
            key="warranties",
            title="Warranties",
            template=(
                "The Seller represents that it has the right to sell the goods or provide "
                "the services described in this Agreement."
            ),
        ),
        Clause(
            key="governing_law",
            title="Governing Law",
            template=(
                "This Agreement shall be governed by {governing_law}."
            ),
            required_fields=["governing_law"],
        ),
    ],
}


def get_clauses_for_contract(contract_type: str) -> List[Clause]:
    return CLAUSE_LIBRARY.get(contract_type, [])


def get_clause_keys(contract_type: str) -> List[str]:
    return [clause.key for clause in get_clauses_for_contract(contract_type)]


def get_clause_by_key(contract_type: str, clause_key: str) -> Optional[Clause]:
    for clause in get_clauses_for_contract(contract_type):
        if clause.key == clause_key:
            return clause
    return None


def render_clause(contract_type: str, clause_key: str, fields: Dict[str, Any]) -> str:
    clause = get_clause_by_key(contract_type, clause_key)
    if not clause:
        return ""
    return clause.render(fields)


def render_all_clauses(contract_type: str, fields: Dict[str, Any]) -> List[Dict[str, str]]:
    rendered = []
    for clause in get_clauses_for_contract(contract_type):
        rendered.append({
            "key": clause.key,
            "title": clause.title,
            "text": clause.render(fields),
        })
    return rendered


def has_clause(contract_type: str, clause_key: str) -> bool:
    return get_clause_by_key(contract_type, clause_key) is not None
