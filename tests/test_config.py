from pathlib import Path

from pdbr.utils import read_config


def test_read_config():
    pdbr_history = str(Path.home() / ".pdbr_history")
    pdbr_history_ipython = str(Path.home() / ".pdbr_history_ipython")

    assert read_config() == (
        "dim",
        None,
        pdbr_history,
        pdbr_history_ipython,
    )
