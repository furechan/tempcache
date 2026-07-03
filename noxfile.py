"""Test matrix for the supported python versions (nox).

    nox            # run tests on all python versions
    nox -l         # list sessions

uv creates the session environments when available (virtualenv fallback).
Lint is not a nox job — run `ruff check` directly.
"""

import nox

nox.options.envdir = ".venv/.nox"
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session(python=["3.10", "3.11", "3.12", "3.13", "3.14"])
def tests(session):
    """Install the package and run its tests."""
    session.env["PYTHONDONTWRITEBYTECODE"] = "1"
    session.install(".", "pytest")
    session.run("python", "-m", "pytest")
