from pdbr.__main__ import read_config, style


def test_read_config():
    read_config()
    assert style == "yellow"
