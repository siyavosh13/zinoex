import hashlib
import random
import string
from pdfminer.high_level import extract_text
import docx


def hash_contract(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_tx_hash():
    return ''.join(random.choices(string.hexdigits.lower(), k=64))


def generate_block_number():
    return random.randint(100000, 999999)


def extract_text_from_pdf(path: str) -> str:
    return extract_text(path)


def extract_text_from_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])
