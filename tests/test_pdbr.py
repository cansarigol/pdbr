import pdb

import pytest

from pdbr._pdbr import rich_pdb_klass


@pytest.fixture
def RichPdb():
    return rich_pdb_klass(pdb.Pdb, show_layouts=False)


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
    RichPdb()._print("msg[tag]")
    captured = capsys.readouterr()
    assert captured.out == "msg\x1b[1m[\x1b[0mtag\x1b[1m]\x1b[0m\n"
