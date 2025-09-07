"""Lightweight JSON schema constants for requests/responses.

No external validator is used to avoid adding new dependencies. These
schemas are documentation-first; endpoints already enforce required
fields and types and return standardized error shapes via error_response.
"""

# Request Schemas
INFERENCE_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["text", "task"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
        "task": {"type": "string", "enum": ["simplify", "summarize", "translate"]},
        "language": {"type": "string"},
        "target_lang": {"type": "string", "enum": ["en", "hi"]},
        "stream": {"type": ["boolean", "string", "number"]},
    },
    "additionalProperties": True,
}

SIMPLE_TEXT_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["text"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
        "stream": {"type": ["boolean", "string", "number"]},
    },
    "additionalProperties": True,
}

TRANSLATE_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["text"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
        "target_lang": {"type": "string", "enum": ["en", "hi"]},
        "stream": {"type": ["boolean", "string", "number"]},
    },
    "additionalProperties": True,
}

FULL_ANALYSIS_REQUEST_SCHEMA = SIMPLE_TEXT_REQUEST_SCHEMA

# Response Schemas (reference only)
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["ok", "error"],
    "properties": {
        "ok": {"type": "boolean", "const": False},
        "error": {
            "type": "object",
            "required": ["code", "message"],
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
        },
    },
}

INFERENCE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["ok", "task", "result"],
    "properties": {
        "ok": {"type": "boolean", "const": True},
        "task": {"type": "string"},
        "result": {"type": "string"},
    },
}

FULL_ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["ok", "mode", "result"],
    "properties": {
        "ok": {"type": "boolean", "const": True},
        "mode": {"type": "string", "const": "full-analysis"},
        "result": {
            "type": "object",
            "required": ["simplified", "summary", "risk"],
            "properties": {
                "simplified": {"type": "string"},
                "summary": {"type": "string"},
                "risk": {"type": "array"},
            },
        },
    },
}
