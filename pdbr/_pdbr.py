from pdb import Pdb

from rich.console import Console
from rich.panel import Panel
from rich.syntax import DEFAULT_THEME, Syntax
from rich.theme import Theme


class RichPdb(Pdb):
    _style = None
    _theme = None

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

        custom_theme = Theme(
            {"info": "dim cyan", "warning": "magenta", "danger": "bold red"}
        )
        self._console = Console(file=self.stdout, theme=custom_theme)

    def do_help(self, arg):
        super().do_help(arg)
        self._print(
            Panel(
                "Click the "
                "[bold][link=https://github.com/cansarigol/pdbr]link[/link][/]"
                " for more!"
            ),
            style="warning",
        )

    do_help.__doc__ = Pdb.do_help.__doc__
    do_h = do_help

    def do_list(self, arg):
        """l(ist)
        List 11 lines source code for the current file.
        """
        try:
            filename = self.curframe.f_code.co_filename
            first = max(1, self.curframe.f_lineno - 5)
            line_range = first, first + 10
            highlight_lines = {self.curframe.f_lineno}
            syntax = Syntax.from_path(
                filename,
                line_numbers=True,
                theme=self._theme or DEFAULT_THEME,
                line_range=line_range,
                highlight_lines=highlight_lines,
            )
            self._print(syntax)
        except BaseException:
            self.error("could not get source code")

    do_l = do_list

    def do_longlist(self, arg):
        """longlist | ll
        List the whole source code for the current function or frame.
        """
        try:
            filename = self.curframe.f_code.co_filename
            highlight_lines = {self.curframe.f_lineno}
            syntax = Syntax.from_path(
                filename,
                line_numbers=True,
                theme=self._theme or DEFAULT_THEME,
                highlight_lines=highlight_lines,
            )
            self._print(syntax)
        except BaseException:
            self.error("could not get source code")

    do_ll = do_longlist

    def displayhook(self, obj):
        if obj is not None:
            self._print(obj)

    def error(self, msg):
        self._print(msg, prefix="***", style="danger")

    def message(self, msg):
        self._print(msg)

    def _print(self, val, prefix=None, style=None):
        args = (prefix, val) if prefix else (val,)

        style = style or self._style
        kwargs = {"style": str(style)} if style else {}

        self._console.print(*args, **kwargs)
