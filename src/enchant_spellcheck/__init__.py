"""Check text files against Enchant dictionaries."""

import re
from pathlib import Path

import click
import enchant  # pyright: ignore[reportMissingTypeStubs]
from enchant.errors import DictNotFoundError

_BACKTICKS = re.compile(
    pattern=r"(?<!`)(?P<ticks>`{1,3})(?!`)[^`]*(?P=ticks)(?!`)"
)
_WORDS = re.compile(pattern=r"\w+(?:['\u2019]\w+)*", flags=re.UNICODE)


def _mask_span(match: re.Match[str]) -> str:
    """Hide a backtick span while preserving source positions."""
    return "".join("\n" if char == "\n" else " " for char in match[0])


@click.command(name="enchant-spellcheck")
@click.argument(
    "files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--known-words",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="UTF-8 file of accepted words, one per line.",
)
@click.option(
    "--language",
    default="en_US",
    show_default=True,
    help="Enchant dictionary language.",
)
@click.version_option(package_name="enchant-spellcheck")
def main(
    files: tuple[Path, ...], known_words: Path | None, language: str
) -> None:
    """Check FILES for unknown words, ignoring backtick spans."""
    try:
        dictionary = enchant.Dict(tag=language)
    except DictNotFoundError as error:
        raise click.UsageError(
            message=f"Cannot load dictionary {language!r}: {error}"
        ) from error

    try:
        accepted: set[str] | frozenset[str] = (
            {
                word.strip()
                for word in known_words.read_text(
                    encoding="utf-8"
                ).splitlines()
                if word.strip() != ""
            }
            if known_words is not None
            else frozenset()
        )
        failed = False
        for file_path in files:
            content = file_path.read_text(encoding="utf-8")
            masked = _BACKTICKS.sub(repl=_mask_span, string=content)
            for line_number, line in enumerate(
                iterable=masked.splitlines(), start=1
            ):
                for match in _WORDS.finditer(string=line):
                    word = match[0]
                    if (
                        word in accepted
                        or word.isdigit()
                        or dictionary.check(word=word)
                    ):
                        continue
                    click.echo(
                        message=(
                            f"{file_path}:{line_number}:{match.start() + 1}: "
                            f"Misspelled word: '{word}'"
                        ),
                        err=True,
                    )
                    failed = True
    except (OSError, UnicodeError) as error:
        raise click.UsageError(message=str(object=error)) from error

    if failed:
        raise click.exceptions.Exit(code=1)
