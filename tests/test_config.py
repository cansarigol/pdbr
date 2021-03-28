import os

from pdbr.utils import read_config


def test_read_config():
    pdbr_history = os.path.join(os.path.expanduser("~"), ".pdbr_history")
    pdbr_history_ipython = os.path.join(
        os.path.expanduser("~"),
        ".pdbr_history_ipython",
    )
    assert read_config() == (
        "dim",
        None,
        pdbr_history,
        pdbr_history_ipython,
    )
