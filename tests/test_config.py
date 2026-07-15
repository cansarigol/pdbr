import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pdbr.logging import get_log_buffer, uninstall_log_capture
from pdbr.utils import read_config

root_dir = Path(__file__).parents[1]


@pytest.fixture
def isolated_tmpdir():
    tmpdir = TemporaryDirectory()
    original_cwd = os.getcwd()
    os.chdir(tmpdir.name)
    yield Path(tmpdir.name)
    os.chdir(original_cwd)


@pytest.fixture(autouse=True)
def cleanup_log_capture():
    yield
    uninstall_log_capture()


@pytest.fixture
def dummy_global_config():
    XDG_CONFIG_HOME = Path.home() / ".config"
    pdbr_dir = XDG_CONFIG_HOME / "pdbr"
    pdbr_dir.mkdir(exist_ok=True, parents=True)
    setup_file = pdbr_dir / "setup.cfg"
    backup_file = pdbr_dir / (setup_file.stem + ".cfg.bak")

    if setup_file.exists():
        setup_file.rename(backup_file)

    with open(setup_file, "wt") as f:
        f.writelines(["[pdbr]\n", "theme = ansi_light"])

    yield setup_file

    setup_file.unlink()

    if backup_file.exists():
        backup_file.rename(setup_file)


def test_global_config(dummy_global_config):
    assert dummy_global_config.exists()

    tmpdir = TemporaryDirectory()
    os.chdir(tmpdir.name)

    # Second element of tuple is theme
    assert read_config()[1] == "ansi_light"
    os.chdir(root_dir)


def test_local_config():
    tmpdir = TemporaryDirectory()
    os.chdir(tmpdir.name)
    setup_file = Path(tmpdir.name) / "setup.cfg"

    with open(setup_file, "wt") as f:
        f.writelines(["[pdbr]\n", "theme = ansi_dark"])

    assert read_config()[1] == "ansi_dark"
    os.chdir(root_dir)


def test_read_config():
    pdbr_history = str(Path.home() / ".pdbr_history")
    pdbr_history_ipython = str(Path.home() / ".pdbr_history_ipython")

    assert read_config() == ("dim", None, pdbr_history, pdbr_history_ipython, None)


def test_log_config_disabled_via_section(isolated_tmpdir):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text("[pdbr.log]\nenabled = False\n")

    read_config()

    root_handler_types = {type(h).__name__ for h in logging.getLogger().handlers}
    assert "RingHandler" not in root_handler_types


def test_log_config_buffer_size_override(isolated_tmpdir):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text("[pdbr.log]\nbuffer_size = 7\n")

    read_config()

    buffer = get_log_buffer()
    assert buffer.maxlen == 7


def test_log_config_level_override(isolated_tmpdir):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text("[pdbr.log]\nlevel = WARNING\n")

    read_config()

    logger = logging.getLogger("pdbr.test.cfglevel")
    logger.debug("dropped")
    logger.warning("kept")

    messages = [entry.message for entry in get_log_buffer()]
    assert "dropped" not in messages
    assert "kept" in messages


def test_traceback_show_locals_defaults_to_false(isolated_tmpdir, mocker):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text("[pdbr]\nuse_traceback = True\n")
    install_mock = mocker.patch("rich.traceback.install")

    read_config()

    install_mock.assert_called_once()
    assert install_mock.call_args.kwargs["show_locals"] is False


def test_traceback_show_locals_enabled_via_config(isolated_tmpdir, mocker):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text(
        "[pdbr]\nuse_traceback = True\ntraceback_show_locals = True\n"
    )
    install_mock = mocker.patch("rich.traceback.install")

    read_config()

    install_mock.assert_called_once()
    assert install_mock.call_args.kwargs["show_locals"] is True


def test_traceback_show_locals_ignored_when_use_traceback_false(
    isolated_tmpdir, mocker
):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text(
        "[pdbr]\nuse_traceback = False\ntraceback_show_locals = True\n"
    )
    install_mock = mocker.patch("rich.traceback.install")

    read_config()

    install_mock.assert_not_called()


def test_use_traceback_defaults_to_true_when_key_absent(isolated_tmpdir, mocker):
    setup_file = isolated_tmpdir / "setup.cfg"
    setup_file.write_text("[pdbr]\ntheme = ansi_dark\n")
    install_mock = mocker.patch("rich.traceback.install")

    read_config()

    install_mock.assert_called_once()
    assert install_mock.call_args.kwargs["show_locals"] is False
