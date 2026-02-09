"""PII detection and redaction guardrails."""

import re

_PATTERNS = {
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        re.IGNORECASE,
    ),
    "PHONE": re.compile(
        r"""
        (?:
            \+?1?[-.\s]?
            (?:\([0-9]{3}\)|[0-9]{3})
            [-.\s]?
            [0-9]{3}
            [-.\s]?
            [0-9]{4}
        )
        """,
        re.VERBOSE,
    ),
    "SSN": re.compile(
        r"\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b"
    ),
    "CARD": re.compile(
        r"""
        \b(?:
            4[0-9]{12}(?:[0-9]{3})?|
            (?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}|
            3[47][0-9]{13}|
            6(?:011|5[0-9]{2})[0-9]{12}|
            [0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}
        )\b
        """,
        re.VERBOSE,
    ),
}

_PLACEHOLDERS = {
    "EMAIL": "[EMAIL]",
    "PHONE": "[PHONE]",
    "SSN": "[SSN]",
    "CARD": "[CARD]",
}


def contains_pii(text: str) -> bool:
    """Check if text contains any PII."""
    return any(pattern.search(text) for pattern in _PATTERNS.values())


def redact_pii(text: str) -> str:
    """Detect and redact PII from text, returning the redacted string."""
    matches = []
    for pii_type, pattern in _PATTERNS.items():
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), pii_type))

    if not matches:
        return text

    matches.sort(key=lambda m: m[0])
    redacted = text
    for start, end, pii_type in reversed(matches):
        redacted = redacted[:start] + _PLACEHOLDERS[pii_type] + redacted[end:]

    return redacted
