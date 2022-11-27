import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pdbr.utils import read_config

root_dir = Path(__file__).parents[1]


@pytest.fixture
def no_global_config():
    XDG_CONFIG_HOME = Path.home() / ".config"
    pdbr_dir = XDG_CONFIG_HOME / "pdbr"
    pdbr_dir.mkdir(exist_ok=True)
    setup_file = pdbr_dir / "setup.cfg"
    backup_file = pdbr_dir / (setup_file.stem + ".cfg.bak")

    if setup_file.exists():
        setup_file.rename(backup_file)

    yield setup_file

    if setup_file.exists():
        setup_file.unlink()

    if backup_file.exists():
        backup_file.rename(setup_file)


@pytest.fixture
def dummy_global_config(no_global_config):
    setup_file = no_global_config

    with open(setup_file, "wt") as f:
        f.writelines(["[pdbr]\n", "theme = ansi_light"])

    yield setup_file


def test_global_config(dummy_global_config):
    try:
        with TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)

            # Second element of tuple is theme
            assert read_config()[1] == "ansi_light"

    finally:
        os.chdir(root_dir)


def test_local_config():
    try:
        with TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            setup_file = Path(tmpdir) / "setup.cfg"

            with open(setup_file, "wt") as f:
                f.writelines(["[pdbr]\n", "theme = ansi_dark"])

            assert read_config()[1] == "ansi_dark"

    finally:
        os.chdir(root_dir)


def test_read_config():
    pdbr_history = str(Path.home() / ".pdbr_history")
    pdbr_history_ipython = str(Path.home() / ".pdbr_history_ipython")

    assert read_config() == (
        "dim",
        None,
        pdbr_history,
        pdbr_history_ipython,
    )
