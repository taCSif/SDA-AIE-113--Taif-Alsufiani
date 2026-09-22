"""Structured JSON logging.

One JSON object per line on stdout, every log emitted while handling a
request carries the same `trace_id` (bound into a contextvar by the
trace/logging middleware in api/app.py), and anything that looks like a
secret — a field named `token`/`password`/`secret`, or a value shaped
like a GitHub PAT or similar API key — is masked before it ever reaches
the log sink. Masking degrades gracefully: it is a backstop for the
mistake of logging a secret directly, not a reason to do so on purpose.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import structlog
from structlog.types import EventDict

# Value SHAPES we mask wherever they appear, even inside a free-text
# message, because a secret doesn't stop being one just because a
# developer interpolated it into a string instead of passing a field.
_SECRET_VALUE_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{36}"),        # GitHub personal access token
    re.compile(r"gh[oprsu]_[A-Za-z0-9]{36}"),  # GitHub OAuth/app/refresh/user-to-server tokens
    re.compile(r"sk-[A-Za-z0-9]{20,}"),        # OpenAI-style secret key
]

# Field NAMES that are secrets by definition — masked regardless of
# what they contain.
_SECRET_KEYS = {"token", "github_token", "password", "secret", "api_key", "authorization"}

MASK = "***MASKED***"

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _mask_string(value: str) -> str:
    for pattern in _SECRET_VALUE_PATTERNS:
        value = pattern.sub(MASK, value)
    return value


def mask_secrets(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """structlog processor: mask known secret fields and known secret
    shapes wherever they appear in the event dict."""
    for key, value in event_dict.items():
        if key.lower() in _SECRET_KEYS:
            event_dict[key] = MASK
        elif isinstance(value, str):
            event_dict[key] = _mask_string(value)
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """Call once, from the composition root, before the first log line
    is emitted."""
    level_num = _LEVELS.get(level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=level_num)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_secrets,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(*args: Any, **kwargs: Any) -> Any:
    return structlog.get_logger(*args, **kwargs)
