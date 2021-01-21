from pdb import Pdb

from rich import box, inspect
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint
from rich.syntax import DEFAULT_THEME, Syntax
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree


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

    def _get_syntax_for_list(self, line_range):
        filename = self.curframe.f_code.co_filename
        highlight_lines = {self.curframe.f_lineno}

        return Syntax.from_path(
            filename,
            line_numbers=True,
            theme=self._theme or DEFAULT_THEME,
            line_range=line_range,
            highlight_lines=highlight_lines,
        )

    def _get_variables(self):
        return [
            (k, str(v), str(type(v)))
            for k, v in self.curframe.f_locals.items()
            if not k.startswith("__") and k != "pdbr"
        ]

    def do_list(self, arg):
        """l(ist)
        List 11 lines source code for the current file.
        """
        try:
            first = max(1, self.curframe.f_lineno - 5)
            line_range = first, first + 10

            self._print(self._get_syntax_for_list(line_range))
        except BaseException:
            self.error("could not get source code")

    do_l = do_list

    def do_longlist(self, arg):
        """longlist | ll
        List the whole source code for the current function or frame.
        """
        try:
            self._print(self._get_syntax_for_list(None))
        except BaseException:
            self.error("could not get source code")

    do_ll = do_longlist

    def do_vars(self, arg):
        """
        List of local variables
        """

        table = Table(title="List of local variables", box=box.MINIMAL)

        table.add_column("Variable", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta", no_wrap=True)
        table.add_column("Type", style="green")
        [
            table.add_row(variable, value, _type)
            for variable, value, _type in self._get_variables()
        ]
        self._print(table)

    do_v = do_vars

    def do_varstree(self, arg):
        """
        List of local variables in Rich.Tree
        """
        tree_key = ""
        type_tree = None
        tree = Tree("Variables")

        for variable, value, _type in sorted(
            self._get_variables(), key=lambda item: (item[2], item[0])
        ):
            if tree_key != _type:
                if tree_key != "":
                    tree.add(type_tree, style="bold green")
                type_tree = Tree(_type)
                tree_key = _type
            type_tree.add(f"{variable}: {value}", style="magenta")
        if type_tree:
            tree.add(type_tree, style="bold green")
        self._print(tree)

    do_vt = do_varstree

    def do_inspect(self, arg, all=False):
        """inspect
        Display the data / methods / docs for any Python object.
        """
        try:
            inspect(self._getval(arg), console=self._console, methods=True, all=all)
        except BaseException:
            pass

    def do_inspectall(self, arg):
        """inspectall
        Inspect with all to see all attributes.
        """
        self.do_inspect(arg, all=True)

    do_i = do_inspect
    do_ia = do_inspectall

    def do_pp(self, arg):
        """pp expression
        Rich pretty print.
        """
        try:
            pprint(self._getval(arg), console=self._console)
        except BaseException:
            pass

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
