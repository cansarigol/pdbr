import inspect
import pdb

import pytest

from pdbr._pdbr import rich_pdb_klass


@pytest.fixture
def RichPdb(*args, **kwargs):
    currentframe = inspect.currentframe()

    def wrapper():
        rpdb = rich_pdb_klass(pdb.Pdb, show_layouts=False)(*args, **kwargs)
        # Set frame and stack related self-attributes
        rpdb.botframe = currentframe.f_back
        rpdb.setup(currentframe.f_back, None)
        return rpdb

    return wrapper


def test_prompt(RichPdb):
    assert RichPdb().prompt == "(Pdbr) "


def test_print(capsys, RichPdb):
    RichPdb()._print("msg")
    captured = capsys.readouterr()
    assert captured.out == "msg\n"


def test_print_error(capsys, RichPdb):
    RichPdb().error("error")
    captured = capsys.readouterr()
    assert captured.out == "\x1b[1;31m*** error\x1b[0m\n"


def test_print_with_style(capsys, RichPdb):
    RichPdb()._print("msg", style="yellow")
    captured = capsys.readouterr()
    assert captured.out == "\x1b[33mmsg\x1b[0m\n"


def test_print_without_escape_tag(capsys, RichPdb):
    RichPdb()._print("[blue]msg[/]")
    captured = capsys.readouterr()
    assert captured.out == "\x1b[34mmsg\x1b[0m\n"


def test_print_array(capsys, RichPdb):
    RichPdb()._print("[[8]]")
    captured = capsys.readouterr()
    assert (
        captured.out == "\x1b[1m[\x1b[0m\x1b[1m[\x1b[0m\x1b[1;36m8"
        "\x1b[0m\x1b[1m]\x1b[0m\x1b[1m]\x1b[0m\n"
    )


def test_onecmd(capsys, RichPdb):
    rpdb = RichPdb()
    cmd = 'print("msg")'
    stop = rpdb.onecmd(cmd)
    captured = capsys.readouterr()
    assert not stop
    assert captured.out == "msg\n"
