import inspect
import logging
import pdb

import pytest

from pdbr._pdbr import rich_pdb_klass
from pdbr.logging import (
    CLEAR_SENTINEL,
    CapturedLog,
    get_log_buffer,
    install_log_capture,
    query_logs,
    uninstall_log_capture,
)


@pytest.fixture
def capture():
    # Reset any handler auto-installed at import time (its level may not
    # match what the test needs — the module-level default is WARNING).
    uninstall_log_capture()
    install_log_capture(buffer_size=100, level=logging.DEBUG)
    yield get_log_buffer()
    uninstall_log_capture()


@pytest.fixture
def RichPdb():
    currentframe = inspect.currentframe()

    def wrapper():
        rpdb = rich_pdb_klass(pdb.Pdb, show_layouts=False)()
        rpdb.botframe = currentframe.f_back
        rpdb.setup(currentframe.f_back, None)
        return rpdb

    return wrapper


def test_captures_stdlib_log_record(capture):
    logging.getLogger("pdbr.test.capture").info("hello world")

    assert len(capture) == 1
    entry = capture[-1]
    assert isinstance(entry, CapturedLog)
    assert entry.level == logging.INFO
    assert entry.logger == "pdbr.test.capture"
    assert entry.message == "hello world"


def test_captures_non_standard_extra_fields(capture):
    logging.getLogger("pdbr.test.extra").info(
        "processing", extra={"task_id": "abc123", "retries": 2}
    )

    entry = capture[-1]
    assert entry.extra == {"task_id": "abc123", "retries": 2}


def test_captures_exception_info(capture):
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("pdbr.test.exc").exception("failed")

    entry = capture[-1]
    assert entry.exc_info is not None
    assert "ValueError: boom" in entry.exc_info


def test_ring_buffer_drops_oldest_when_full():
    install_log_capture(buffer_size=3, level=logging.DEBUG)
    try:
        logger = logging.getLogger("pdbr.test.ring")
        for i in range(5):
            logger.info("msg-%d", i)

        buffer = get_log_buffer()
        assert len(buffer) == 3
        assert [entry.message for entry in buffer] == ["msg-2", "msg-3", "msg-4"]
    finally:
        uninstall_log_capture()


def test_level_filter_at_install_time():
    install_log_capture(buffer_size=100, level=logging.WARNING)
    try:
        logger = logging.getLogger("pdbr.test.level")
        logger.debug("debug-drop")
        logger.info("info-drop")
        logger.warning("warning-keep")
        logger.error("error-keep")

        messages = [entry.message for entry in get_log_buffer()]
        assert messages == ["warning-keep", "error-keep"]
    finally:
        uninstall_log_capture()


def test_install_is_idempotent():
    install_log_capture(buffer_size=100, level=logging.DEBUG)
    try:
        first_handler_count = len(logging.getLogger().handlers)
        install_log_capture(buffer_size=999, level=logging.WARNING)
        assert len(logging.getLogger().handlers) == first_handler_count
        # Second call must not swap the buffer either.
        logging.getLogger("pdbr.test.idem").debug("still-captured")
        assert any(entry.message == "still-captured" for entry in get_log_buffer())
    finally:
        uninstall_log_capture()


def test_uninstall_removes_handler():
    install_log_capture(buffer_size=100, level=logging.DEBUG)
    handler_count_before = len(logging.getLogger().handlers)
    uninstall_log_capture()

    handler_count_after = len(logging.getLogger().handlers)
    assert handler_count_after == handler_count_before - 1
    assert list(get_log_buffer()) == []


def test_install_with_enabled_false_is_noop():
    install_log_capture(enabled=False)

    assert list(get_log_buffer()) == []
    logging.getLogger("pdbr.test.disabled").warning("should-not-capture")
    assert list(get_log_buffer()) == []


def test_default_level_does_not_bump_root_logger():
    uninstall_log_capture()
    original_level = logging.getLogger().level
    try:
        install_log_capture(buffer_size=10)
        assert logging.getLogger().level == original_level
    finally:
        uninstall_log_capture()


def test_do_log_shows_placeholder_when_buffer_empty(capsys, RichPdb, capture):
    RichPdb().do_log("")

    assert "No log records captured" in capsys.readouterr().out


def test_do_log_renders_table_with_captured_records(capsys, RichPdb, capture):
    logging.getLogger("pdbr.test.render").warning("something broke")

    RichPdb().do_log("")

    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "pdbr.test.render" in output
    assert "something broke" in output


def test_do_log_filter_by_level(capsys, RichPdb, capture):
    logger = logging.getLogger("pdbr.test.filter.level")
    logger.debug("d-message")
    logger.error("e-message")

    RichPdb().do_log("--level warning")

    output = capsys.readouterr().out
    assert "d-message" not in output
    assert "e-message" in output


def test_do_log_filter_by_contains(capsys, RichPdb, capture):
    logger = logging.getLogger("pdbr.test.filter.contains")
    logger.info("alpha payload")
    logger.info("beta payload")

    RichPdb().do_log("--contains alpha")

    output = capsys.readouterr().out
    assert "alpha payload" in output
    assert "beta payload" not in output


def test_do_log_filter_by_logger(capsys, RichPdb, capture):
    logging.getLogger("celery.worker").info("celery event")
    logging.getLogger("django.request").info("django event")

    RichPdb().do_log("--logger celery")

    output = capsys.readouterr().out
    assert "celery event" in output
    assert "django event" not in output


def test_do_log_count_limits_output(capsys, RichPdb, capture):
    logger = logging.getLogger("pdbr.test.count")
    for i in range(10):
        logger.info("record-%d", i)

    RichPdb().do_log("2")

    output = capsys.readouterr().out
    assert "record-8" in output
    assert "record-9" in output
    assert "record-0" not in output


def test_do_log_clear_empties_buffer(capsys, RichPdb, capture):
    logging.getLogger("pdbr.test.clear").info("will-be-cleared")
    assert len(capture) == 1

    RichPdb().do_log("clear")

    assert len(capture) == 0


def test_do_log_reports_unknown_argument(capsys, RichPdb, capture):
    RichPdb().do_log("--bogus foo")

    output = capsys.readouterr().out
    assert "Unknown argument" in output


def test_do_log_reports_missing_flag_value(capsys, RichPdb, capture):
    RichPdb().do_log("--level")

    output = capsys.readouterr().out
    assert "Missing value for --level" in output


def test_do_log_reports_unknown_level(capsys, RichPdb, capture):
    RichPdb().do_log("--level bogus")

    output = capsys.readouterr().out
    assert "Unknown log level" in output


def test_percent_magic_does_not_replay_via_emptyline(capsys, RichPdb, capture):
    logging.getLogger("pdbr.test.replay").warning("only-once")

    rpdb = RichPdb()
    rpdb.precmd("%log --contains only-once")
    first_render = capsys.readouterr().out
    assert first_render.count("only-once") == 1
    assert rpdb.lastcmd == ""

    rpdb.precmd("")
    second_render = capsys.readouterr().out
    assert "only-once" not in second_render


def test_query_logs_returns_records_and_renderable(capture):
    logging.getLogger("pdbr.test.query").info("hello")

    records, renderable = query_logs("")

    assert len(records) == 1
    assert records[0].message == "hello"
    assert renderable is not None


def test_query_logs_clear_returns_sentinel(capture):
    logging.getLogger("pdbr.test.query.clear").info("before-clear")
    assert len(capture) == 1

    assert query_logs("clear") is CLEAR_SENTINEL
    assert len(capture) == 0


def test_query_logs_raises_on_bad_arg(capture):
    with pytest.raises(ValueError, match="Unknown argument"):
        query_logs("--nope value")


def test_captured_log_repr_pretty_produces_one_line():
    class PrinterSpy:
        def __init__(self):
            self.buffer = []

        def text(self, chunk):
            self.buffer.append(chunk)

    entry = CapturedLog(
        ts=__import__("datetime").datetime.now(),
        level=logging.WARNING,
        logger="pdbr.test.repr",
        message="watch out",
    )
    spy = PrinterSpy()
    entry._repr_pretty_(spy, cycle=False)

    rendered = "".join(spy.buffer)
    assert rendered == "<CapturedLog WARNING pdbr.test.repr: watch out>"


def test_do_log_exposes_last_log_when_shell_is_available(capsys, capture):
    try:
        from IPython.terminal.debugger import TerminalPdb
    except ImportError:
        pytest.skip("IPython not available")

    currentframe = inspect.currentframe()
    ripdb = rich_pdb_klass(TerminalPdb, show_layouts=False)()
    ripdb.botframe = currentframe.f_back
    ripdb.setup(currentframe.f_back, None)

    logging.getLogger("pdbr.test.ipython.last").info("keep-me")
    ripdb.do_log("--logger pdbr.test.ipython.last")

    assert "_last_log" in ripdb.shell.user_ns
    last = ripdb.shell.user_ns["_last_log"]
    assert [entry.message for entry in last] == ["keep-me"]


def test_ipython_magic_registers_and_executes(capsys, capture):
    IPython = pytest.importorskip("IPython")
    from IPython.testing.globalipapp import get_ipython

    from pdbr.ipython_magics import register_pdbr_ipython_magics

    ip = get_ipython()
    assert ip is not None
    assert register_pdbr_ipython_magics(ip) is True

    logging.getLogger("pdbr.test.ipymagic").warning("magical")

    ip.run_line_magic("log", "--contains magical")

    assert "_last_log" in ip.user_ns
    records = ip.user_ns["_last_log"]
    assert any(entry.message == "magical" for entry in records)
    del IPython


def test_ipython_magic_clear_via_magic(capsys, capture):
    pytest.importorskip("IPython")
    from IPython.testing.globalipapp import get_ipython

    from pdbr.ipython_magics import register_pdbr_ipython_magics

    ip = get_ipython()
    register_pdbr_ipython_magics(ip)

    logging.getLogger("pdbr.test.ipyclear").info("will-clear")
    assert len(capture) >= 1

    ip.run_line_magic("log", "clear")
    assert len(capture) == 0


def test_ipython_magic_reports_bad_arg(capsys, capture):
    pytest.importorskip("IPython")
    from IPython.testing.globalipapp import get_ipython

    from pdbr.ipython_magics import register_pdbr_ipython_magics

    ip = get_ipython()
    register_pdbr_ipython_magics(ip)

    ip.run_line_magic("log", "--level bogus")

    output = capsys.readouterr().out
    assert "Unknown log level" in output
