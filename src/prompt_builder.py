"""
prompt_builder.py
-----------------
Loads reusable prompt templates and safely constructs final prompts
by inserting validated user inputs. All variable substitution uses
Python string .format_map() with a SafeDict to catch missing keys.

Design rationale:
- Templates live in prompts/ directory, not in code, so they can be
  reviewed, versioned, and updated without touching Python logic.
- SafeDict leaves unrecognized keys as-is, making template errors
  visible rather than silently producing broken prompts.
- sanitized_preview() strips system instructions so users can inspect
  the prompt structure without exposing internal directives.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class SafeDict(dict):
    """dict subclass that returns '{key}' for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def load_template(template_name: str) -> str:
    """
    Load a prompt template file from the prompts/ directory.
    Raises FileNotFoundError if the template does not exist.
    """
    path = PROMPTS_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt template '{template_name}' not found in {PROMPTS_DIR}"
        )
    return path.read_text(encoding="utf-8")


def build_prompt(template_name: str, variables: dict[str, Any]) -> str:
    """
    Load a template and substitute variables safely.
    Comment lines (starting with #) and the SYSTEM: / USER: labels
    are preserved in the full prompt but can be split for display.

    Returns the complete prompt string with variables substituted.
    Missing variables are left as {variable_name} placeholders.
    """
    template = load_template(template_name)
    # Convert all values to strings for safe substitution
    str_vars = {k: str(v) if v is not None else "" for k, v in variables.items()}
    return template.format_map(SafeDict(str_vars))


def extract_user_section(prompt: str) -> str:
    """
    Extract only the USER: section of a prompt for display.
    Strips comment lines and SYSTEM: section.
    """
    lines = prompt.splitlines()
    in_user = False
    user_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("USER:"):
            in_user = True
            continue
        if stripped.startswith("SYSTEM:"):
            in_user = False
            continue
        if in_user:
            user_lines.append(line)
    return "\n".join(user_lines).strip()


def get_template_metadata(template_name: str) -> dict:
    """
    Parse comment header lines from a template file to extract metadata
    (ID, version, purpose, required variables, safety constraints).
    """
    try:
        template = load_template(template_name)
    except FileNotFoundError:
        return {}
    metadata = {}
    for line in template.splitlines():
        if not line.startswith("# "):
            break
        if ":" in line:
            key, _, value = line[2:].partition(":")
            metadata[key.strip().lower().replace(" ", "_")] = value.strip()
    return metadata


def sanitized_preview(template_name: str, variables: dict[str, Any]) -> str:
    """
    Build a sanitized preview prompt for display in the Prompt Inspector.
    Shows the USER: section with variables substituted.
    Does NOT expose SYSTEM: instructions or comment metadata.
    """
    full_prompt = build_prompt(template_name, variables)
    return extract_user_section(full_prompt)


def get_all_template_names() -> list[str]:
    """Return a list of all .txt template file names in the prompts directory."""
    if not PROMPTS_DIR.exists():
        return []
    return sorted(p.name for p in PROMPTS_DIR.glob("*.txt"))
