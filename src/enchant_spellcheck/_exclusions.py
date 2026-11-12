"""Mask excluded text while preserving source positions."""

import re

BACKTICKS: re.Pattern[str] = re.compile(
    pattern=r"(?<!`)(?P<ticks>`{1,3})(?!`)[^`]*(?P=ticks)(?!`)"
)


def mask_text(content: str) -> str:
    """Replace excluded characters with spaces, retaining newlines."""
    return "".join("\n" if char == "\n" else " " for char in content)


def _mask_span(match: re.Match[str]) -> str:
    """Hide a backtick span while preserving source positions."""
    return mask_text(content=match[0])


def mask_backticks(content: str) -> str:
    """Hide text enclosed in matching backticks."""
    return BACKTICKS.sub(repl=_mask_span, string=content)
