"""Staging and warehouse loaders."""

import re

_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _safe_identifier(name: str) -> str:
    """Validate that a string is a safe SQL identifier (lowercase alphanumeric + underscores).

    Raises ValueError if the name does not match the allowed pattern.
    """
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name
