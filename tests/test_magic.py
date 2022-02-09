import inspect
import os
import re
import sys
from pathlib import Path

import pexpect
import pytest
from pexpect import spawn
from rich.console import Console
from rich.theme import Theme

from pdbr._pdbr import rich_pdb_klass

NUMBER_RE = "[\d.e+_,-]+"  # Matches 1e+03, 1.0e-03, 1_000, 1,000

TAG_RE = re.compile(r"\x1b[\[\]]+[\dDClhJt;?]+m?")


def untag(s):
    """Not perfect, but does the job.
    >>> untag('\x1b[0mfoo\x1b[0m\x1b[0;34m(\x1b[0m\x1b[0marg\x1b[0m\x1b[0;34m)\x1b[0m\x1b[0;34m\x1b[0m\x1b[0;34m\x1b[0m\x1b[0m')
    'foo(arg)'
    """
    s = s.replace("\x07", "")
    s = s.replace("\x1b[?2004l", "")
    return TAG_RE.sub("", s)


@pytest.fixture
def pdbr_child_process(tmp_path) -> spawn:
    """
    Spawn a pdbr prompt in a child process.
    """
    file = tmp_path / "foo.py"
    file.write_text("breakpoint()")
    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"
    child = pexpect.spawn(
        str(Path(sys.executable).parent / "pdbr"),
        [str(file)],
        env=env,
        encoding="utf-8",
    )
    child.expect("foo.py")
    child.expect("breakpoint")
    child.sendeof()
    # child = replwrap.REPLWrapper(f"{sys.executable} -m pdbr {str(file)}",
    #                              ".*",
    #                              ".*",
    #                              '',
    #                              )
    # child.run_command("\n")
    # child.run_command("\n")
    # fout = open('mylog.txt', 'w')
    # child.logfile_read = fout
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
            file=kwargs.get("stdout", sys.stdout),
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


def test_onecmd_time_line_magic(capsys, RichIPdb):
    RichIPdb().onecmd("%time pass")
    captured = capsys.readouterr()
    output = captured.out
    assert re.search(
        rf"CPU times: user {NUMBER_RE} [mµn]s, sys: {NUMBER_RE} [mµn]s, total: {NUMBER_RE} [mµn]s\n"
        rf"Wall time: {NUMBER_RE} [mµn]s",
        output,
    )


def test_onecmd_unsupported_cell_magic(capsys, RichIPdb):
    RichIPdb().onecmd("%%time pass")
    captured = capsys.readouterr()
    output = captured.out
    error = f"Cell magics (multiline) are not yet supported. Use a single '%' instead."
    assert output == "*** " + error + "\n"
    cmd = "%%time"
    stop = RichIPdb().onecmd(cmd)
    captured_output = capsys.readouterr().out
    assert not stop
    RichIPdb().error(error)
    cell_magics_error = capsys.readouterr().out
    assert cell_magics_error == captured_output


def test_onecmd_lsmagic_line_magic(capsys, RichIPdb):
    RichIPdb().onecmd("%lsmagic")
    captured = capsys.readouterr()
    output = captured.out

    assert re.search(
        "Available line magics:\n%alias +%alias_magic +%autoawait.*%%writefile",
        output,
        re.DOTALL,
    )


def test_no_zombie_lastcmd(capsys, RichIPdb):
    rpdb = RichIPdb(stdout=sys.stdout)
    rpdb.onecmd("print('SHOULD_NOT_BE_IN_%pwd_OUTPUT')")
    captured = capsys.readouterr()
    assert captured.out.endswith(
        "SHOULD_NOT_BE_IN_%pwd_OUTPUT\n"
    )  # Starts with colors and prompt
    rpdb.onecmd("%pwd")
    captured = capsys.readouterr()
    assert captured.out.endswith(Path.cwd().absolute().as_posix() + "\n")
    assert "SHOULD_NOT_BE_IN_%pwd_OUTPUT" not in captured.out


def test_TerminalPdb_magics_override(tmp_path, capsys, RichIPdb):
    from IPython.utils.text import dedent

    tmp_file = tmp_path / "foo.py"
    tmp_file_content = '''def foo(arg):
    """Bar docstring"""
    pass
    '''
    tmp_file.write_text(tmp_file_content)

    rpdb = RichIPdb(stdout=sys.stdout)
    rpdb.onecmd(f'import sys; sys.path.append("{tmp_file.parent.absolute()}")')
    rpdb.onecmd(f"from {tmp_file.stem} import foo")

    # pdef
    rpdb.do_pdef("foo")
    do_pdef_foo_output = capsys.readouterr().out
    untagged = untag(do_pdef_foo_output).strip()
    assert untagged.endswith("foo(arg)"), untagged
    rpdb.onecmd("%pdef foo")
    magic_pdef_foo_output = capsys.readouterr().out
    untagged = untag(magic_pdef_foo_output).strip()
    assert untagged.endswith("foo(arg)"), untagged

    # pdoc
    rpdb.onecmd("%pdoc foo")
    magic_pdef_foo_output = capsys.readouterr().out
    untagged = untag(magic_pdef_foo_output).strip()
    expected_docstring = dedent(
        """Class docstring:
        Bar docstring
    Call docstring:
        Call self as a function."""
    )
    assert untagged == expected_docstring, untagged

    # pfile
    rpdb.onecmd("%pfile foo")
    magic_pfile_foo_output = capsys.readouterr().out
    untagged = untag(magic_pfile_foo_output).strip()
    tmp_file_content = Path(tmp_file).read_text().strip()
    assert untagged == tmp_file_content

    # pinfo
    rpdb.onecmd("%pinfo foo")
    magic_pinfo_foo_output = capsys.readouterr().out
    untagged = untag(magic_pinfo_foo_output).strip()
    expected_pinfo = dedent(
        f"""Signature: foo(arg)
    Docstring: Bar docstring
    File:      {tmp_file.absolute()}
    Type:      function"""
    )
    assert untagged == expected_pinfo, untagged

    # pinfo2
    rpdb.onecmd("%pinfo2 foo")
    magic_pinfo2_foo_output = capsys.readouterr().out
    untagged = untag(magic_pinfo2_foo_output).strip()
    expected_pinfo2 = re.compile(
        dedent(
            rf"""Signature: foo\(arg\)
    Source:\s*
    %s
    File:      {tmp_file.absolute()}
    Type:      function"""
        )
        % re.escape(tmp_file_content)
    )
    assert expected_pinfo2.fullmatch(untagged), untagged

    # psource
    rpdb.onecmd("%psource foo")
    magic_psource_foo_output = capsys.readouterr().out
    untagged = untag(magic_psource_foo_output).strip()
    expected_psource = '''def foo(arg):
    """Bar docstring"""
    pass'''
    assert untagged == expected_psource, untagged


def test_expr_questionmark_pinfo(tmp_path, capsys, RichIPdb):
    from IPython.utils.text import dedent

    tmp_file = tmp_path / "foo.py"
    tmp_file_content = '''def foo(arg):
    """Bar docstring"""
    pass
    '''
    tmp_file.write_text(tmp_file_content)

    rpdb = RichIPdb(stdout=sys.stdout)
    rpdb.onecmd(f'import sys; sys.path.append("{tmp_file.parent.absolute()}")')
    rpdb.onecmd(f"from {tmp_file.stem} import foo")

    # pinfo
    rpdb.onecmd(rpdb.precmd("foo?"))
    magic_foo_qmark_output = capsys.readouterr().out
    untagged = untag(magic_foo_qmark_output).strip()
    expected_pinfo = re.compile(
        dedent(
            f"""Signature: foo\(arg\)
    Docstring: Bar docstring
    File:      /tmp/.*/foo.py
    Type:      function"""
        )
    )
    assert expected_pinfo.fullmatch(untagged), untagged

    # pinfo2
    rpdb.onecmd(rpdb.precmd("foo??"))
    magic_foo_qmark2_output = capsys.readouterr().out
    rpdb.onecmd(rpdb.precmd("%pinfo2 foo"))
    magic_pinfo2_foo_output = capsys.readouterr().out
    assert magic_pinfo2_foo_output == magic_foo_qmark2_output
