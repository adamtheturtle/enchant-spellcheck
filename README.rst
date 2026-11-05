enchant-spellcheck
==================

Check UTF-8 text files against an Enchant dictionary, with an optional list of accepted words.
Unknown words fail the command, making it suitable for continuous integration.
Text enclosed in matching single, double, or triple backticks is ignored, including across lines.
This supports checking prose containing inline code or template placeholders.

Installation
------------

Install Enchant and a dictionary first.
On macOS:

.. code-block:: shell

   brew install enchant

On Ubuntu:

.. code-block:: shell

   sudo apt-get install libenchant-2-2 hunspell-en-us

PyEnchant's Windows wheels include Enchant and English dictionaries.
See the `PyEnchant installation guide <https://pyenchant.github.io/pyenchant/install.html>`_ for other platforms and languages.
Then install this package:

.. code-block:: shell

   uv tool install enchant-spellcheck

Usage
-----

.. code-block:: shell

   enchant-spellcheck document.txt
   enchant-spellcheck --known-words spelling_private_dict.txt document.txt other.txt
   enchant-spellcheck --language en_GB document.txt
   python -m enchant_spellcheck document.txt

The accepted-words file contains one word per line.
Blank lines are ignored and matching is case sensitive.
Diagnostics contain the filename, line, column, and misspelled word, in source order.
Exit status is 0 for valid text, 1 for spelling mistakes, and 2 for invalid arguments, unavailable dictionaries, or unreadable files.
Results depend on the installed system dictionary.

Words are Unicode letters, numbers, or underscores, with internal straight or curly apostrophes preserved.
Numeric tokens are ignored, while words with unmatched backticks are checked.
The checker treats its input as text without parsing document formats or extracting code blocks.

Use with doccmd
---------------

Check prose inside documentation code blocks with `doccmd <https://github.com/adamtheturtle/doccmd>`_:

.. code-block:: shell

   doccmd --language=text --skip-marker=spelling --use-pty=no --command="enchant-spellcheck --known-words=spelling_private_dict.txt" guide.rst

Development
-----------

The project setup follows `doccmd <https://github.com/adamtheturtle/doccmd>`_, including setuptools-scm versions, uv dependency groups, prek hooks, strict type checking, Sphinx documentation, and Towncrier release notes.
See the `contribution guide <https://adamtheturtle.github.io/enchant-spellcheck/contributing.html>`_ and `release process <https://adamtheturtle.github.io/enchant-spellcheck/release-process.html>`_.
