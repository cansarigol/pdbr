import os
import sys
import typing
from pdb import Pdb

from rich.console import Console

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


class RichPdb(Pdb):
    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        skip=None,
        nosigint=False,
        readrc=True,
    ):
        super().__init__(completekey, stdin, stdout, skip, nosigint, readrc)
        self.prompt = "(Pdbr) "

    def _print(self, val, prefix=None, style=None):
        args = (prefix, val) if prefix else (val,)
        kwargs = {"style": str(style)} if style else {}
        Console(file=self.stdout).print(*args, **kwargs)

    def do_rp(self, arg):
        """rp expression
        Rich-print with style.
        """
        try:
            val = self._getval(arg)
            style = "5"
            if isinstance(val, typing.Iterable) and len(val) == 2:
                val, style = val
            self._print(val, style=style)
        except BaseException:
            pass

    def displayhook(self, obj):
        if obj is not None:
            self._print(obj)

    def error(self, msg):
        self._print(msg, prefix="***", style="red")


def set_trace(*, header=None, context=None):
    pdb = RichPdb()
    if header is not None:
        pdb.message(header)
    pdb.set_trace(sys._getframe().f_back)


def run(statement, globals=None, locals=None):
    RichPdb().run(statement, globals, locals)


if os.environ.get("USE_RICH_TRACEBACK", False):
    from rich.traceback import install

    theme = os.environ.get("PYGMENTS_THEME", "friendly")
    install(theme=theme)
