# /usr/bin/env python3

"""
Nox files are an easy way to automate testing in different virtual environments. It
will automatically create virtual environments and install required packages.
"""

from typing import Iterable

import nox

# Default sessions to run when just `nox` is run in the project
nox.options.sessions = ["lint"]


# Lånt fra: https://github.com/cjolowicz/cookiecutter-hypermodern-python-instance/blob/90e45cee4725c51c77864ab21efead23d5226306/noxfile.py#L26-L51
def install(session: nox.Session, *, groups: Iterable[str], root: bool = True) -> None:
    """Install the dependency groups using Poetry.

    This function installs the given dependency groups into the session's
    virtual environment. When ``root`` is true (the default), the function
    also installs the root package and its default dependencies.

    To avoid an editable install, the root package is not installed using
    ``poetry install``. Instead, the function invokes ``pip install .``
    to perform a PEP 517 build.

    Args:
        session: The Session object.
        groups: The dependency groups to install.
        root: Install the root package.
    """
    session.run_always(
        "poetry",
        "install",
        "--no-root",
        "--sync",
        "--{}={}".format("only" if not root else "with", ",".join(groups)),
        external=True,
    )
    if root:
        session.install(".")


@nox.session  # type: ignore[misc]
def lint(session: nox.Session) -> None:
    """Run pre-commit"""
    install(session, groups=["lint"], root=False)
    session.run("pre-commit", "run", "--all-files", "--show-diff-on-failure")


@nox.session  # type: ignore[misc]
def fix(session: nox.Session) -> None:
    """
    Run ruff to fix errors and format, then run linters
    """
    install(session, groups=["lint"], root=False)
    session.run("ruff", "check", "--fix", ".")
    session.run("ruff", "format", ".")
    # Run linting after fixing to warn about mypy
    session.notify("lint")
