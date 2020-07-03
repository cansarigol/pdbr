from pdb import Pdb

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme


class RichPdb(Pdb):
    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        skip=None,
        nosigint=False,
        readrc=True,
        default_style=None,
    ):
        super().__init__(completekey, stdin, stdout, skip, nosigint, readrc)
        self.prompt = "(Pdbr) "
        self.style = default_style

        custom_theme = Theme(
            {"info": "dim cyan", "warning": "magenta", "danger": "bold red"}
        )
        self._console = Console(file=self.stdout, theme=custom_theme)

    def do_help(self, arg):
        super().do_help(arg)
        self._print(
            Panel(
                "Click [bold][link=https://github.com/cansarigol/pdbr]link[/link][/]"
                " for more!"
            ),
            style="warning",
        )

    do_help.__doc__ = Pdb.do_help.__doc__
    do_h = do_help

    def displayhook(self, obj):
        if obj is not None:
            self._print(obj)

    def error(self, msg):
        self._print(msg, prefix="***", style="danger")

    def message(self, msg):
        self._print(msg)

    def _print(self, val, prefix=None, style=None):
        args = (prefix, val) if prefix else (val,)

        style = style or self.style
        kwargs = {"style": str(style)} if style else {}

        self._console.print(*args, **kwargs)
