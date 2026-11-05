"""Exercise the CLI against real Enchant dictionaries."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from enchant_spellcheck import main

_USAGE_ERROR = 2


@pytest.mark.parametrize(
    argnames="content",
    argvalues=[
        "Hello world.\n",
        "123 456\n",
        "don't isn't\n",
        "Hello `zzspeling` world\n",
        "Hello ``zzspeling`` world\n",
        "Hello ```zzspeling``` world\n",
        "Hello `zzspeling\nzzwrong` world\n",
        "Hello ``zzspeling\nzzwrong`` world\n",
        "Hello ```zzspeling\nzzwrong``` world\n",
        "",
    ],
)
def test_valid_text(tmp_path: Path, content: str) -> None:
    """Valid words, numbers, and matching backtick spans pass."""
    document = tmp_path / "document.txt"
    _ = document.write_text(data=content, encoding="utf-8")
    result = CliRunner().invoke(cli=main, args=[str(object=document)])
    assert result.exit_code == 0, result.output
    assert result.output == ""


def test_positions_and_order(tmp_path: Path) -> None:
    """Diagnostics retain positions after exclusions and follow source
    order.
    """
    document = tmp_path / "document.txt"
    _ = document.write_text(
        data="`zzignored\nzzignored` zzsecond\nzzfirst zzfirst\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli=main, args=[str(object=document)])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.splitlines() == [
        f"{document}:2:12: Misspelled word: 'zzsecond'",
        f"{document}:3:1: Misspelled word: 'zzfirst'",
        f"{document}:3:9: Misspelled word: 'zzfirst'",
    ]


def test_known_words(tmp_path: Path) -> None:
    """Accepted words are stripped, blank lines ignored, and case
    preserved.
    """
    document = tmp_path / "document.txt"
    words = tmp_path / "words.txt"
    _ = document.write_text(data="zzcustom Zzcustom", encoding="utf-8")
    _ = words.write_text(data="\n  zzcustom  \n\n", encoding="utf-8")
    result = CliRunner().invoke(
        cli=main,
        args=["--known-words", str(object=words), str(object=document)],
    )
    assert result.exit_code == 1
    assert result.stderr == f"{document}:1:10: Misspelled word: 'Zzcustom'\n"


def test_multiple_files(tmp_path: Path) -> None:
    """All supplied files are checked even after a misspelling is
    found.
    """
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    _ = first.write_text(data="zzfirst", encoding="utf-8")
    _ = second.write_text(data="zzsecond", encoding="utf-8")
    result = CliRunner().invoke(
        cli=main, args=[str(object=first), str(object=second)]
    )
    assert result.exit_code == 1
    assert result.stderr.splitlines() == [
        f"{first}:1:1: Misspelled word: 'zzfirst'",
        f"{second}:1:1: Misspelled word: 'zzsecond'",
    ]


@pytest.mark.parametrize(
    argnames="content",
    argvalues=[
        "`zzwrong",
        "zzwrong`",
        "``zzwrong`",
        "````zzwrong````",
        "zz_wrong",
        "zzdon\u2019t",
    ],
)
def test_unknown_tokens(tmp_path: Path, content: str) -> None:
    """Unmatched delimiters and unknown Unicode tokens remain checked."""
    document = tmp_path / "document.txt"
    _ = document.write_text(data=content, encoding="utf-8")
    result = CliRunner().invoke(cli=main, args=[str(object=document)])
    assert result.exit_code == 1
    assert "Misspelled word:" in result.stderr


def test_missing_dictionary(tmp_path: Path) -> None:
    """An unavailable dictionary produces an actionable usage error."""
    document = tmp_path / "document.txt"
    document.touch()
    result = CliRunner().invoke(
        cli=main, args=["--language=zz_ZZ", str(object=document)]
    )
    assert result.exit_code == _USAGE_ERROR
    assert "zz_ZZ" in result.stderr


@pytest.mark.parametrize(
    argnames="invalid_file", argvalues=["document", "known_words"]
)
def test_invalid_utf8(tmp_path: Path, invalid_file: str) -> None:
    """Invalid document or accepted-word encoding produces a usage
    error.
    """
    document = tmp_path / "document.txt"
    words = tmp_path / "words.txt"
    _ = document.write_bytes(
        data=b"\xff" if invalid_file == "document" else b"Hello"
    )
    _ = words.write_bytes(
        data=b"\xff" if invalid_file == "known_words" else b""
    )
    result = CliRunner().invoke(
        cli=main,
        args=["--known-words", str(object=words), str(object=document)],
    )
    assert result.exit_code == _USAGE_ERROR
    assert "Error:" in result.stderr


@pytest.mark.parametrize(
    argnames="args",
    argvalues=[
        [],
        ["missing-file.txt"],
        ["--known-words=missing.txt", "missing-file.txt"],
    ],
)
def test_invalid_arguments(args: list[str]) -> None:
    """Missing files and arguments fail with usage errors."""
    result = CliRunner().invoke(cli=main, args=args)
    assert result.exit_code == _USAGE_ERROR


@pytest.mark.parametrize(argnames="option", argvalues=["--help", "--version"])
def test_information(option: str) -> None:
    """Help and version are available without input files."""
    result = CliRunner().invoke(cli=main, args=[option])
    assert result.exit_code == 0
    assert "enchant-spellcheck" in result.output
