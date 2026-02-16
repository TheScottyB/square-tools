"""Auth and token loading helpers."""

from __future__ import annotations

from pathlib import Path
import os


DEFAULT_ENV_FILE = Path.home() / ".config" / "claude-mcp" / ".env"


def _load_env_file(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_file.exists():
        return values

    for raw_line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def resolve_square_token(explicit_token: str | None = None, env_file: Path | None = None) -> str:
    """Return Square token from explicit arg, env vars, or local env-file."""
    if explicit_token:
        return explicit_token

    env_token = os.environ.get("SQUARE_ACCESS_TOKEN") or os.environ.get("SQUARE_TOKEN")
    if env_token:
        return env_token

    lookup_file = env_file or DEFAULT_ENV_FILE
    values = _load_env_file(lookup_file)
    token = values.get("SQUARE_ACCESS_TOKEN") or values.get("SQUARE_TOKEN")
    if not token:
        raise RuntimeError(
            "Square token not found. Set SQUARE_ACCESS_TOKEN or SQUARE_TOKEN, "
            f"or add one to {lookup_file}."
        )
    return token
