"""Exclude Jinja syntax without rendering or validating templates."""

import re

from enchant_spellcheck._exclusions import BACKTICKS, mask_backticks, mask_text

_OPEN = re.compile(pattern=BACKTICKS.pattern + r"|{[{%#]")
_RAW = re.compile(pattern=r"{%[+-]?\s*raw\s*[+-]?%}")
_END_RAW = re.compile(pattern=r"{%[+-]?\s*endraw\s*[+-]?%}")
_CLOSING = {"{{": "}}", "{%": "%}", "{#": "#}"}
_BRACKETS = {"(": ")", "[": "]", "{": "}"}


def _unterminated(content: str, start: int, kind: str) -> ValueError:
    """Describe an unfinished construct at its original source
    position.
    """
    line = content.count("\n", 0, start) + 1
    column = start - content.rfind("\n", 0, start)
    return ValueError(
        f"Unterminated Jinja {kind} at line {line}, column {column}"
    )


def _tag_end(content: str, start: int) -> int:
    """Find a closing delimiter outside strings and expression
    brackets.
    """
    opening = content[start : start + 2]
    closing = _CLOSING[opening]
    position = start + 2
    quote = ""
    brackets: list[str] = []
    while position < len(content):
        char = content[position]
        if opening == "{#":
            if content.startswith(closing, position):
                return position + 2
        elif quote != "":
            if char == "\\":
                position += 2
                continue
            if char == quote:
                quote = ""
        elif len(brackets) == 0 and content.startswith(closing, position):
            return position + 2
        elif char in "\"'":
            quote = char
        elif char in _BRACKETS:
            brackets.append(_BRACKETS[char])
        elif len(brackets) > 0 and char == brackets[-1]:
            _ = brackets.pop()
        position += 1
    raise _unterminated(content=content, start=start, kind="tag")


def mask_jinja(content: str) -> str:
    """Hide default Jinja tags and comments, retaining literal raw content."""
    parts: list[str] = []
    position = 0
    while (opening := _OPEN.search(string=content, pos=position)) is not None:
        start = opening.start()
        end = (
            opening.end()
            if opening[0].startswith("`")
            else _tag_end(content=content, start=start)
        )
        parts.extend(
            (content[position:start], mask_text(content=content[start:end]))
        )
        if _RAW.fullmatch(string=content, pos=start, endpos=end) is not None:
            closing = _END_RAW.search(string=content, pos=end)
            if closing is None:
                raise _unterminated(
                    content=content, start=start, kind="raw block"
                )
            parts.extend(
                (
                    mask_backticks(content=content[end : closing.start()]),
                    mask_text(content=closing[0]),
                )
            )
            end = closing.end()
        position = end
    parts.append(content[position:])
    return "".join(parts)
