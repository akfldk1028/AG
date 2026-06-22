"""
OAuth token management for Claude Agent SDK.

Extracted from model_factory.py:39-72.
Handles Claude Max subscription OAuth tokens (sk-ant-oat01-*).
"""

import json
import os
from typing import Optional

_TOKEN_PREFIX = "sk-ant-oat01-"


def get_oauth_token() -> Optional[str]:
    """
    Retrieve Claude Max OAuth token.

    Priority:
    1. CLAUDE_CODE_OAUTH_TOKEN environment variable
    2. Windows credential files (~/.claude/.credentials.json etc.)

    Returns:
        OAuth token string or None if not found.
    """
    # Environment variable first
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token and validate_token(token):
        return token

    # Credential file paths (Windows + Unix/macOS)
    home = os.path.expanduser("~")
    cred_paths = [
        os.path.join(home, ".claude", ".credentials.json"),
        os.path.join(home, ".claude", "credentials.json"),
        os.path.expandvars(r"%LOCALAPPDATA%\Claude\credentials.json"),
        os.path.expandvars(r"%APPDATA%\Claude\credentials.json"),
        os.path.join(home, ".config", "claude", "credentials.json"),
    ]

    for cred_path in cred_paths:
        try:
            if os.path.exists(cred_path):
                with open(cred_path, encoding="utf-8") as f:
                    data = json.load(f)
                token = data.get("claudeAiOauth", {}).get("accessToken")
                if token and validate_token(token):
                    return token
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            continue

    return None


def validate_token(token: str) -> bool:
    """Check if token has valid Claude OAuth prefix."""
    return isinstance(token, str) and token.startswith(_TOKEN_PREFIX)
