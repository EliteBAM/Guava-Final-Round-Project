"""
Loads the project's .env file (KEY=VALUE lines, in Application/ or the repo root) into the environment. My helper, not a Guava API.

Only main.py's __main__ and `python -m esign` call it: tests never do, so a test run can't send texts or create
DocuSign envelopes. Settings are listed in Documents/Documents and CRM Data Notes/Documents and Data Stack.md.
"""

import os
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
# either place works; both are gitignored by the ".env" rule
ENV_FILES = (APP_DIR / ".env", REPO_ROOT / ".env")

# an unquoted value ends at " #": the rest of the line is a comment
INLINE_COMMENT = re.compile(r"\s+#.*$")


def load_env_file(*paths: Path) -> None:
    """Loads Application/.env and the repo root's .env. Variables already set in the environment win."""
    for path in paths or ENV_FILES:
        _load(path)


def _load(path: Path) -> None:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()  # -sig: PowerShell writes a BOM
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        key = key.removeprefix("export ").strip()  # shell-style lines work too
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = INLINE_COMMENT.sub("", value)
        os.environ.setdefault(key, value)


def repo_path(value: str) -> Path:
    """A path from .env: relative paths are tried from the repo root, then from Application/."""
    path = Path(value)
    if path.is_absolute() or (REPO_ROOT / path).exists():
        return path if path.is_absolute() else REPO_ROOT / path
    return APP_DIR / path
