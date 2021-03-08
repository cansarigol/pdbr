from pdbr.utils import read_config


def test_read_config():
    assert read_config() == ("dim", None)
