import os
import nox
import tempfile

ENVDIR = os.path.join(tempfile.gettempdir(), "nox")
# USE_CONDA = os.getenv("CONDA_DEFAULT_ENV")
USE_CONDA = False

nox.options.envdir = ENVDIR

if USE_CONDA:
    nox.options.default_venv_backend = "conda"


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8", "src")


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
def tests(session: nox.Session):
    session.install('.', 'pytest')
    session.run('pytest')
