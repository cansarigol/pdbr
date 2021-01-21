from pdbr.__main__ import _read_config


def test_read_config():
    assert _read_config() == ("dim", None)
