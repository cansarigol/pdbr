import inspect
import os
import re
import sys

import pexpect
import pytest
from pexpect import spawn
from rich.console import Console
from rich.theme import Theme

from pdbr._pdbr import rich_pdb_klass

NUMBER_RE = "[\d.e+_,-]+"  # Matches 1e+03, 1.0e-03, 1_000, 1,000


@pytest.fixture
def pdbr_child_process(tmp_path) -> spawn:
    file = tmp_path / "foo.py"
    file.write_text("breakpoint()")
    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"
    child = pexpect.spawn(sys.executable, ["-m", "pdbr", str(file)], env=env)
    child.timeout = 3
    return child


@pytest.fixture
def RichIPdb():
    """
    In contrast to the normal RichPdb in test_pdbr.py which inherits from
    built-in pdb.Pdb, this one inherits from IPython's TerminalPdb, which holds
    a 'shell' attribute that is a IPython TerminalInteractiveShell.
    This is required for the magic commands to work (and happens automatically
    when the user runs pdbr when IPython is importable).
    """
    from IPython.terminal.debugger import TerminalPdb

    currentframe = inspect.currentframe()

    def rich_ipdb_klass(*args, **kwargs):
        ripdb = rich_pdb_klass(TerminalPdb, show_layouts=False)(*args, **kwargs)
        # Set frame and stack related self-attributes
        ripdb.botframe = currentframe.f_back
        ripdb.setup(currentframe.f_back, None)
        # Set the console's file to stdout so that we can capture the output
        _console = Console(
            file=sys.stdout,
            theme=Theme(
                {"info": "dim cyan", "warning": "magenta", "danger": "bold red"}
            ),
        )
        ripdb._console = _console
        return ripdb

    return rich_ipdb_klass


@pytest.mark.slow
class TestPdbrChildProcess:
    def test_time(self, pdbr_child_process):
        pdbr_child_process.sendline("from time import sleep")
        pdbr_child_process.sendline("%time sleep(0.1)")
        pdbr_child_process.expect("CPU time")
        pdbr_child_process.expect("Wall time: 100 ms")

    def test_timeit(self, pdbr_child_process):
        pdbr_child_process.sendline("%timeit -n 1 -r 1 pass")
        pdbr_child_process.expect_exact("std. dev. of 1 run, 1 loop each)")


def test_precmd_time_line_magic(capsys, RichIPdb):
    RichIPdb().precmd("%time pass")
    captured = capsys.readouterr()
    output = captured.out
    assert re.search(
        rf"CPU times: user {NUMBER_RE} [mµn]s, sys: {NUMBER_RE} [mµn]s, total: {NUMBER_RE} [mµn]s\n"
        rf"Wall time: {NUMBER_RE} [mµn]s",
        output,
    )


def test_precmd_unsupported_cell_magic(capsys, RichIPdb):
    RichIPdb().precmd("%%time pass")
    captured = capsys.readouterr()
    output = captured.out
    assert (
        output
        == f"*** Cell magics (multiline) are not yet supported. Use a single '%' instead.\n"
    )
    cmd = "%%ls"
    line = RichIPdb().precmd(cmd)
    captured_output = capsys.readouterr().out
    assert line == ""
    RichIPdb().error(
        "Cell magics (multiline) are not yet supported. Use a single '%' instead."
    )
    cell_magics_error = capsys.readouterr().out
    assert cell_magics_error == captured_output
