""" tasks file (see invoke.py) """

import toml
import logging

from invoke import task
from pathlib import Path

logger = logging.getLogger()

root_folder = Path(__file__).parent


def get_config(folder):
    """ Parse pyproject.toml file """

    pyproject = folder.joinpath("pyproject.toml").resolve()

    if not pyproject.exists():
        raise FileNotFoundError(str(pyproject))

    return toml.load(pyproject)


@task
def clean(ctx):
    """ Clean build and dist folders """
    patterns = ['build', 'dist']
    for pattern in patterns:
        ctx.run("rm -rf {}".format(pattern))


@task
def build(ctx):
    """ Build wheel with python -mbuild """

    ctx.run("python -mbuild --wheel")


@task
def publish(ctx, test_only=False):
    """ Publish project with twine """

    if test_only:
        ctx.run("twine upload --repository testpypi dist/*")
    else:
        ctx.run("twine upload dist/*")
