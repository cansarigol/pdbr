import inspect
import io
import re
from pathlib import Path
from pdb import Pdb, getsourcelines

from rich import box, markup
from rich._inspect import Inspect
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint
from rich.syntax import DEFAULT_THEME, Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.tree import Tree

from pdbr._console_layout import ConsoleLayout

try:
    from IPython.terminal.interactiveshell import TerminalInteractiveShell

    TerminalInteractiveShell.simple_prompt = False
except ImportError:
    pass

WITHOUT_LAYOUT_COMMANDS = (
    "where",
    "w",
)
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class AsciiStdout(io.TextIOWrapper):
    pass


def rich_pdb_klass(base, is_celery=False, context=None, show_layouts=True):
    class RichPdb(base):
        _style = None
        _theme = None
        _history_file = None
        _ipython_history_file = None
        _latest_search_arg = ""

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

        def pt_init(self, pt_session_options=None):
            from prompt_toolkit.history import FileHistory

            if self._ipython_history_file:
                self.shell.debugger_history = FileHistory(self._ipython_history_file)
            func = super().pt_init
            func_args = inspect.getargspec(super().pt_init).args
            if "pt_session_options" in func_args:
                func(pt_session_options)
            else:
                func()

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
                    force_terminal=True,
                    force_interactive=True,
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
                    print_layout=False,
                    dont_escape=True,
                )

        do_help.__doc__ = base.do_help.__doc__
        do_h = do_help

        def _get_syntax_for_list(self, with_line_range=False):
            line_range = None
            if with_line_range:
                first = max(1, self.curframe.f_lineno - 5)
                line_range = first, first + 10
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

        def do_l(self, arg):
            """l
            List 11 lines source code for the current file.
            """
            try:
                self._print(
                    self._get_syntax_for_list(with_line_range=True), print_layout=False
                )
            except BaseException:
                self.error("could not get source code")

        def do_longlist(self, arg):
            """longlist | ll
            List the whole source code for the current function or frame.
            """
            try:
                self._print(self._get_syntax_for_list(), print_layout=False)
            except BaseException:
                self.error("could not get source code")

        do_ll = do_longlist

        def do_search(self, arg):
            """search | src
            Search a phrase in the current frame.
            In order to repeat the last one, type `/` character as arg.
            """
            if not arg or (arg == "/" and not self._latest_search_arg):
                self.error("Search failed: arg is missing")
                return

            if arg == "/":
                arg = self._latest_search_arg
            else:
                self._latest_search_arg = arg

            lines, lineno = getsourcelines(self.curframe)
            indexes = [index for index, line in enumerate(lines, lineno) if arg in line]

            if len(indexes) > 0:
                bigger_indexes = [
                    index for index in indexes if index > self.curframe.f_lineno
                ]
                next_line = bigger_indexes[0] if bigger_indexes else indexes[0]
                return super().do_jump(next_line)
            else:
                self.error(f"Search failed: '{arg}' not found")

        do_src = do_search

        def get_varstable(self):
            variables = self._get_variables()
            if not variables:
                return
            table = Table(title="List of local variables", box=box.MINIMAL)

            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Type", style="green")
            [
                table.add_row(variable, value, _type)
                for variable, value, _type in variables
            ]
            return table

        def do_vars(self, arg):
            """v(ars)
            List of local variables
            """
            self._print(self.get_varstable(), print_layout=False)

        do_v = do_vars

        def get_varstree(self):
            variables = self._get_variables()
            if not variables:
                return
            tree_key = ""
            type_tree = None
            tree = Tree("Variables")

            for variable, value, _type in sorted(
                variables, key=lambda item: (item[2], item[0])
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
            self._print(self.get_varstree(), print_layout=False)

        do_vt = do_varstree

        def do_inspect(self, arg, all=False):
            """(i)nspect
            Display the data / methods / docs for any Python object.
            """
            try:
                self._print(
                    Inspect(self._getval(arg), methods=True, all=all),
                    print_layout=False,
                )
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
                from icecream import ic

                val = self._getval(arg)
                ic.configureOutput(prefix="🍦 |> ")
                self._print(ic.format(arg, val))
            except BaseException:
                pass

        do_ic = do_icecream

        def do_syntax(self, arg):
            """syn(tax)[ val,lexer ]
            Display lexer. https://pygments.org/docs/lexers/
            """
            try:
                val, lexer = arg.split(",")
                val = val.strip()
                lexer = lexer.strip()
                val = Syntax(
                    self._getval(val),
                    self._getval(lexer),
                    theme=self._theme or DEFAULT_THEME,
                )
                self._print(val)
            except BaseException:
                pass

        do_syn = do_syntax

        def do_sql(self, arg):
            """sql
            Display value in sql format.
            """
            self.do_syntax(f"{arg},'sql'")

        def displayhook(self, obj):
            if obj is not None:
                self._print(obj)

        def error(self, msg):
            self._print(msg, prefix="***", style="danger", print_layout=False)

        def _format_stack_entry(self, frame_lineno):
            stack_entry = Pdb.format_stack_entry(self, frame_lineno, "\n")
            return stack_entry.replace(str(Path.cwd().absolute()), "")

        def stack_trace(self):
            stacks = []
            try:
                for frame_lineno in self.stack:
                    frame, _ = frame_lineno
                    if frame is self.curframe:
                        prefix = "-> "
                    else:
                        prefix = "  "

                    stack_entry = self._format_stack_entry(frame_lineno)
                    first_line, _ = stack_entry.splitlines()
                    text_body = Text(stack_entry)
                    text_prefix = Text(prefix)
                    text_body.stylize("bold", len(first_line), len(stack_entry))
                    text_prefix.stylize("bold")
                    stacks.append(Text.assemble(text_prefix, text_body))
            except KeyboardInterrupt:
                pass
            return reversed(stacks)

        def message(self, msg):
            self._print(msg)

        def _print(
            self, val, prefix=None, style=None, print_layout=True, dont_escape=False
        ):
            if val == "--Return--":
                return

            if isinstance(val, str) and dont_escape is False:
                val = markup.escape(val)

            kwargs = {"style": str(style)} if style else {}
            args = (prefix, val) if prefix else (val,)
            if (
                show_layouts
                and print_layout
                and self.lastcmd not in WITHOUT_LAYOUT_COMMANDS
            ):
                self._print_layout(*args, **kwargs)
            else:
                self.console.print(*args, **kwargs)

        def _print_layout(self, val, **kwargs):
            ConsoleLayout(self.console).print(
                val,
                code=self._get_syntax_for_list(),
                stack_trace=self.stack_trace(**kwargs),
                vars=self.get_varstree(),
                **kwargs,
            )

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
