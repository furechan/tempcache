""" IPython extension to remove user name/path from cell outputs """


import re

from pathlib import Path

from IPython.display import display
from IPython.utils.capture import capture_output
from IPython.core.magic import Magics, magics_class, line_cell_magic

from IPython.core.getipython import get_ipython


def sanitize_string(text: str, username: str = "aaaa"):
    """ Utility function to remove username from string """
    pattern = r"(?i)\b%s\b" % re.escape(username)
    return re.sub(pattern, "...", text)


def sanitize_display(value, p, cycle):
    """ IPython custom display handler """
    text = sanitize_string(repr(value))
    p.text(text)
    return text


@magics_class
class SanitizeMagics(Magics):

    @line_cell_magic
    def sanitize(self, line, cell=None):
        """ cell magic to sanitize outputs """
        cell = cell if cell else line
        shell = get_ipython()

        with capture_output() as c:
            shell.run_cell(cell)

        if c.stdout:
            output = sanitize_string(c.stdout)
            print(output)

        for output in c.outputs:
            display(output)


def load_ipython_extension(ipython):
    ipython.register_magics(SanitizeMagics)

    text_formatter = ipython.display_formatter.formatters['text/plain']
    text_formatter.for_type(str, sanitize_display)
    text_formatter.for_type(Path, sanitize_display)
