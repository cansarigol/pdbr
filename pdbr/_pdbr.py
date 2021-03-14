import io
import re
from pdb import Pdb

from icecream import ic
from rich import box
from rich._inspect import Inspect
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.pretty import pprint
from rich.syntax import DEFAULT_THEME, Syntax
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree

LOCAL_VARS_CMD = ("nn", "uu", "dd", "ss")
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class AsciiStdout(io.TextIOWrapper):
    pass


def rich_pdb_klass(base, is_celery=False, context=None):
    class RichPdb(base):
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
            init_kwargs = (
                {"out": stdout}
                if is_celery
                else {
                    "completekey": completekey,
                    "stdin": stdin,
                    "stdout": stdout,
                    "skip": skip,
                    "nosigint": nosigint,
                    "readrc": readrc,
                }
            )
            if context is not None:
                if base == Pdb:
                    raise ValueError("Context can only be used with IPython")
                init_kwargs["context"] = context
            super().__init__(**init_kwargs)

            self.prompt = "(Pdbr) "

        @property
        def console(self):
            if not hasattr(self, "_console"):
                self._console = Console(
                    file=(
                        AsciiStdout(buffer=self.stdout.buffer, encoding="ascii")
                        if is_celery
                        else self.stdout
                    ),
                    theme=Theme(
                        {"info": "dim cyan", "warning": "magenta", "danger": "bold red"}
                    ),
                    style=self._style,
                )
            return self._console

        def do_help(self, arg):
            super().do_help(arg)
            if not arg:
                self._print(
                    Panel(
                        "Visit "
                        "[bold][link=https://github.com/cansarigol/pdbr]"
                        "https://github.com/cansarigol/pdbr[/link][/]"
                        " for more!"
                    ),
                    style="warning",
                )

        do_help.__doc__ = base.do_help.__doc__
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
            try:
                return [
                    (k, str(v), str(type(v)))
                    for k, v in self.curframe.f_locals.items()
                    if not k.startswith("__") and k != "pdbr"
                ]
            except AttributeError:
                return []

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
            """v(ars)
            List of local variables
            """

            table = Table(title="List of local variables", box=box.MINIMAL)

            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Type", style="green")
            [
                table.add_row(variable, value, _type)
                for variable, value, _type in self._get_variables()
            ]
            self._print(table)

        do_v = do_vars

        def get_varstree(self):
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
            return tree

        def do_varstree(self, arg):
            """varstree | vt
            List of local variables in Rich.Tree
            """
            self._print(self.get_varstree())

        do_vt = do_varstree

        def do_inspect(self, arg, all=False):
            """(i)nspect
            Display the data / methods / docs for any Python object.
            """
            try:
                self._print(Inspect(self._getval(arg), methods=True, all=all))
            except BaseException:
                pass

        def do_inspectall(self, arg):
            """inspectall | ia
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
                pprint(self._getval(arg), console=self.console)
            except BaseException:
                pass

        def do_icecream(self, arg):
            """ic(ecream) expression
            Icecream print.
            """
            try:
                val = self._getval(arg)
                ic.configureOutput(prefix="🍦 |> ")
                self._print(ic.format(arg, val))
            except BaseException:
                pass

        do_ic = do_icecream

        def do_uu(self, arg):
            """uu
            Same with u(p) command + with local variables.
            """
            return self.do_up(arg)

        def do_dd(self, arg):
            """dd
            Same with d(own) command + with local variables.
            """
            return self.do_down(arg)

        def do_nn(self, arg):
            """nn
            Same with n(ext) command + with local variables.
            """

            return self.do_next(arg)

        def do_ss(self, arg):
            """ss
            Same with s(tep) command + with local variables.
            """

            return self.do_step(arg)

        def displayhook(self, obj):
            if obj is not None:
                self._print(obj)

        def error(self, msg):
            self._print(msg, prefix="***", style="danger")

        def _make_layout(self):
            if not hasattr(self, "layout"):
                layout = Layout()
                left_layout = Layout(name="left", ratio=2)
                right_layout = Layout(name="right")
                layout.split(left_layout, right_layout, direction="horizontal")
                self.layout = layout
            return self.layout

        def message(self, msg):
            if self.lastcmd in LOCAL_VARS_CMD:
                layout = self._make_layout()
                layout["left"].update(msg)
                layout["right"].update(Panel(self.get_varstree()))
                self._print(layout)
            else:
                self._print(msg)

        def _print(self, val, prefix=None, style=None):
            args = (prefix, val) if prefix else (val,)
            kwargs = {"style": str(style)} if style else {}

            self.console.print(*args, **kwargs)

        def print_stack_entry(self, frame_lineno, prompt_prefix="\n-> ", context=None):
            """
            Remove ipython color format.
            """
            if base == Pdb or is_celery:
                Pdb.print_stack_entry(self, frame_lineno, prompt_prefix)
                return
            self.message(
                ANSI_ESCAPE.sub("", self.format_stack_entry(frame_lineno, "", context))
            )

            # vds: >>
            frame, lineno = frame_lineno
            filename = frame.f_code.co_filename
            self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
            # vds: <<

    return RichPdb
