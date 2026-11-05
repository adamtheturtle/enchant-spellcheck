"""Check template exclusions through the CLI with real dictionaries."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from enchant_spellcheck import main

_USAGE_ERROR = 2


@pytest.mark.parametrize(
    argnames="content",
    argvalues=[
        "",
        "Hello world.",
        "Hello world.\n{%- endif %}\n",
        "{%+ endif +%}",
        "{{ zzvariable | zzfilter }}",
        "{{- zzvariable -}}",
        "{%\nset zzvariable = 'zzvalue'\n%}Hello",
        "{#- zzcomment\n{{ zzvariable }} {% endif %} ' -#}Hello",
        '{{ "zzvalue }} still inside" }}',
        "{% set zzvariable = 'zzvalue %} still inside' %}",
        r"{{ 'zzvalue \' }} still inside' }}",
        r'{{ "zzvalue \\" }}',
        "{{ {'zzkey': {'zznested': 1}}}}",
        "{{ zzcall([1, 2], {'zzkey': 'zzvalue'}) }}",
        "{% raw %}Hello world.{% endraw %}",
        "{%+ raw -%}Hello world.{%- endraw +%}{{ zzvariable }}",
        "`{{ zzignored` Hello world.",
        "Hello ``{% zzignored`` world.",
        "{% if zzcondition %}`zzignored`{% endif %}",
        '{{ "`" }}Hello `zzignored` world.',
        '{# "` #}Hello `zzignored` world.',
        '{% raw %}{{ "`" }}{% endraw %}Hello `zzignored` world.',
    ],
)
def test_jinja_exclusions(tmp_path: Path, content: str) -> None:
    """Syntax is ignored without requiring a balanced template."""
    document = tmp_path / "document.txt"
    _ = document.write_text(data=content, encoding="utf-8")
    result = CliRunner().invoke(
        cli=main, args=["--template=jinja", str(object=document)]
    )
    assert result.exit_code == 0, result.output
    assert result.output == ""


@pytest.mark.parametrize(
    argnames=("content", "diagnostics"),
    argvalues=[
        (
            "{% if zzcondition %}zzfirst{% else %}zzsecond{% endif %}",
            [(1, 21, "zzfirst"), (1, 38, "zzsecond")],
        ),
        ("{{-\nzzvariable\n-}} zzoutside", [(3, 5, "zzoutside")]),
        ('{{ "zzvalue }} inside" }} zzoutside', [(1, 27, "zzoutside")]),
        ("{# zzcomment #}zzoutside", [(1, 16, "zzoutside")]),
        ("{% raw %}{{ zzliteral }}{% endraw %}", [(1, 13, "zzliteral")]),
        (
            "{% raw %}\n{{ zzliteral\n{% endraw %} zzoutside",
            [(2, 4, "zzliteral"), (3, 14, "zzoutside")],
        ),
        (
            "{% raw %}zzfirst{% raw %}zzsecond{% endraw %}",
            [(1, 10, "zzfirst"), (1, 26, "zzsecond")],
        ),
        ("{% raw %}`zzignored` zzoutside{% endraw %}", [(1, 22, "zzoutside")]),
        (
            "`zzignored\nzzignored` {{ zzvariable }} zzoutside",
            [(2, 29, "zzoutside")],
        ),
        ("Hello { world } zzoutside", [(1, 17, "zzoutside")]),
    ],
)
def test_jinja_prose_positions(
    tmp_path: Path, content: str, diagnostics: list[tuple[int, int, str]]
) -> None:
    """Branches and raw text retain exact positions after exclusions."""
    document = tmp_path / "document.txt"
    _ = document.write_text(data=content, encoding="utf-8")
    result = CliRunner().invoke(
        cli=main, args=["--template=jinja", str(object=document)]
    )
    assert result.exit_code == 1, result.output
    assert result.stdout == ""
    assert result.stderr.splitlines() == [
        f"{document}:{line}:{column}: Misspelled word: '{word}'"
        for line, column, word in diagnostics
    ]


@pytest.mark.parametrize(
    argnames=("content", "kind"),
    argvalues=[
        ("{%", "tag"),
        ("{{", "tag"),
        ("{#", "tag"),
        ("{# zzcomment", "tag"),
        ("{{ 'zzvalue }}", "tag"),
        ('{{ "zzvalue ' + "\\", "tag"),
        ("{{ [zzvalue }}", "tag"),
        ("{% raw %}Hello", "raw block"),
    ],
)
def test_unterminated_jinja(tmp_path: Path, content: str, kind: str) -> None:
    """Unfinished constructs report input errors at their opening tag."""
    document = tmp_path / "document.txt"
    _ = document.write_text(data="Hello\n  " + content, encoding="utf-8")
    result = CliRunner().invoke(
        cli=main, args=["--template=jinja", str(object=document)]
    )
    assert result.exit_code == _USAGE_ERROR
    assert (
        f"{document}: Unterminated Jinja {kind} at line 2, column 3"
        in result.stderr
    )


def test_jinja_is_opt_in(tmp_path: Path) -> None:
    """Ordinary text still reports template keywords as unknown words."""
    document = tmp_path / "document.txt"
    _ = document.write_text(
        data="Hello world.\n{%- endif %}\n", encoding="utf-8"
    )
    result = CliRunner().invoke(cli=main, args=[str(object=document)])
    assert result.exit_code == 1
    assert result.stderr == f"{document}:2:5: Misspelled word: 'endif'\n"


def test_jinja_multiple_files_and_known_words(tmp_path: Path) -> None:
    """Template mode composes with accepted words and multiple files."""
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    words = tmp_path / "words.txt"
    _ = first.write_text(data="{{ zzvariable }}zzfirst", encoding="utf-8")
    _ = second.write_text(data="{# zzcomment #}zzsecond", encoding="utf-8")
    _ = words.write_text(data="zzfirst\n", encoding="utf-8")
    result = CliRunner().invoke(
        cli=main,
        args=[
            "--template=jinja",
            "--known-words",
            str(object=words),
            str(object=first),
            str(object=second),
        ],
    )
    assert result.exit_code == 1
    assert result.stderr == f"{second}:1:16: Misspelled word: 'zzsecond'\n"
