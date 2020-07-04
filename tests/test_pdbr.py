from pdbr._pdbr import RichPdb


def test_prompt():
    assert RichPdb().prompt == "(Pdbr) "


def test_print(capsys):
    pdb = RichPdb()
    pdb._print("msg")
    captured = capsys.readouterr()
    assert captured.out == "msg\n"


def test_print_error(capsys):
    pdb = RichPdb()
    pdb.error("error")
    captured = capsys.readouterr()
    assert captured.out == "*** error\n"


def test_print_with_style(capsys):
    pdb = RichPdb()
    pdb._print("msg", style="yellow")
    captured = capsys.readouterr()
    assert captured.out == "msg\n"
