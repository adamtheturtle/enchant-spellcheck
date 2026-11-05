enchant-spellcheck
==================

Check UTF-8 text files against an Enchant dictionary.
Unknown words fail the command, while text enclosed in matching backticks is ignored.

Installation
------------

Install `Enchant and a dictionary <https://pyenchant.github.io/pyenchant/install.html>`_, then:

.. code-block:: shell

   uv tool install enchant-spellcheck

Usage
-----

.. code-block:: shell

   enchant-spellcheck document.txt
   enchant-spellcheck --known-words words.txt document.txt other.txt
   enchant-spellcheck --language en_GB document.txt
   enchant-spellcheck --template=jinja document.txt

- The accepted-words file contains one word per line and matching is case sensitive.
- Diagnostics include the filename, line, column, and misspelled word.
- Exit status is 0 for valid text, 1 for misspellings, and 2 for usage or input errors.
- Results depend on the installed dictionary.

Jinja templates
---------------

Use ``--template=jinja`` to ignore statements (``{% ... %}``), expressions (``{{ ... }}``), and comments (``{# ... #}``).
Tags can span multiple lines and contain quoted delimiters or white space control markers.
Prose in every branch and literal content inside ``{% raw %} ... {% endraw %}`` remain checked.
Backtick spans remain ignored, and diagnostics retain their original line and column positions.

This mode recognizes exclusions without rendering or validating the template.
Standalone tags such as ``{%- endif %}`` are accepted.
Tags, strings, and raw blocks must be closed; otherwise, the command exits with status 2.
Strings inside statements and expressions are ignored, even when they contain prose.
Custom delimiters and line statements are not supported.
