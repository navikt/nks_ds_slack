# /usr/bin/env python3

"""
Nox files are an easy way to automate testing in different virtual environments. It
will automatically create virtual environments and install required packages.
"""

import nox

# Default sessions to run when just `nox` is run in the project
nox.options.sessions = ["lint"]


@nox.session  # type: ignore[misc]
def lint(session: nox.Session) -> None:
    """Run pre-commit"""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", "--show-diff-on-failure")


@nox.session  # type: ignore[misc]
def fix(session: nox.Session) -> None:
    """
    Run ruff to fix errors and format, then run linters
    """
    session.install("ruff")
    session.run("ruff", "check", "--fix", ".")
    session.run("ruff", "format", ".")
    # Run linting after fixing to warn about mypy
    session.notify("lint")
