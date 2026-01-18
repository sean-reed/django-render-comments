"""Nox configuration for testing against multiple Python and Django versions."""

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]
DJANGO_VERSIONS = ["4.2", "5.0", "5.1", "5.2", "6.0"]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session: nox.Session, django: str) -> None:
    """Run the test suite against a matrix of Python and Django versions."""
    # Django 6.0+ requires Python 3.12+
    if django >= "6.0" and session.python in ("3.10", "3.11"):
        session.skip(f"Django {django} requires Python 3.12+")

    session.install("-e", ".", "pytest", "pytest-django", "pytest-cov", f"django~={django}.0")
    session.run("pytest", *session.posargs)


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run linting checks."""
    session.install("-e", ".", "ruff")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")


@nox.session(python="3.12")
def typecheck(session: nox.Session) -> None:
    """Run type checking."""
    session.install("-e", ".", "pyright", "pytest", "pytest-django")
    session.run("pyright")
