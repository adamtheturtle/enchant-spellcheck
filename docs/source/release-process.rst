Release process
===============

The release workflow follows doccmd's calendar versions, Towncrier notes, setuptools-scm packaging, and PyPI trusted publishing.
Native binaries and additional package-manager distributions are not configured.

One-time setup
--------------

Configure a pending trusted publisher on PyPI for project ``enchant-spellcheck``, owner ``adamtheturtle``, repository ``enchant-spellcheck``, workflow ``release.yml``, and environment ``release``.
The release workflow uses OpenID Connect and does not require a PyPI token.

Create the GitHub ``release`` environment and restrict deployments to ``main``.
Enable GitHub Pages with GitHub Actions as its build source.

As in doccmd, configure a ``RELEASE_PAT`` repository secret belonging to an administrator who can bypass the required checks for the generated release commit.
The token needs repository contents write access.
Release commits and tags use this token so their pushes trigger CI and documentation deployment.
The standard workflow token creates the GitHub release.

Publishing
----------

Write release notes in ``newsfragments/+name.change.md`` or ``newsfragments/<issue>.change.md``.
Run the Release workflow from ``main`` once its CI and lint checks have passed.
It validates the source, calculates a calendar version, commits the notes, tags that commit, builds and checks distributions, publishes to PyPI, and creates a GitHub release.
If another commit advances ``main`` before the release commit is pushed, the push fails.
Reconcile and validate again before retrying.

After publication, verify installation from PyPI and update consuming repositories to the published version.
