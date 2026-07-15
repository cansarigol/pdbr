import inspect
import os
import pdb
import sys

import pytest

from pdbr._pdbr import rich_pdb_klass
from pdbr.whereami import (
    _collect_frame,
    _walk_frame_locals_for,
    collect_context,
    render_whereami,
)


@pytest.fixture
def RichPdb():
    currentframe = inspect.currentframe()

    def wrapper():
        rpdb = rich_pdb_klass(pdb.Pdb, show_layouts=False)()
        rpdb.botframe = currentframe.f_back
        rpdb.setup(currentframe.f_back, None)
        return rpdb

    return wrapper


@pytest.fixture
def no_frameworks(monkeypatch):
    top_level = ("django", "celery", "opentelemetry", "structlog")
    for module_name in list(sys.modules):
        parent = module_name.split(".", 1)[0]
        if parent in top_level:
            monkeypatch.setitem(sys.modules, module_name, None)
    for name in top_level:
        monkeypatch.setitem(sys.modules, name, None)


def test_collect_context_always_returns_runtime_process_frame(no_frameworks):
    frame = inspect.currentframe()

    context = collect_context(frame)

    assert context["runtime"]["python"].startswith(
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    assert context["runtime"]["cwd"] == os.getcwd()
    assert context["process"]["pid"] == os.getpid()
    assert context["frame"]["file"].endswith("test_whereami.py")


def test_collect_context_frame_none_yields_none_frame(no_frameworks):
    context = collect_context(None)

    assert context["frame"] is None


def test_collect_context_skips_all_optional_sections_when_absent(no_frameworks):
    context = collect_context(inspect.currentframe())

    assert context["django"] is None
    assert context["celery"] is None
    assert context["opentelemetry"] is None
    assert context["structlog"] is None


def test_collect_frame_reports_file_line_function():
    def sample_target():
        return _collect_frame(inspect.currentframe())

    info = sample_target()

    assert info["file"].endswith("test_whereami.py")
    assert info["function"].endswith("sample_target")
    assert isinstance(info["line"], int)


def test_walk_frame_locals_finds_value_in_outer_frame():
    sentinel = object()

    def inner():
        return _walk_frame_locals_for(inspect.currentframe(), "sentinel")

    def outer():
        outer_sentinel = sentinel  # noqa: F841
        return _walk_frame_locals_for(inspect.currentframe(), "outer_sentinel")

    assert outer() is sentinel
    assert inner() is sentinel


def test_walk_frame_locals_returns_none_when_missing():
    assert _walk_frame_locals_for(inspect.currentframe(), "___never_defined___") is None


def test_render_whereami_empty_context_returns_placeholder_text():
    from rich.text import Text

    rendered = render_whereami({})

    assert isinstance(rendered, Text)
    assert "no context" in rendered.plain


def test_render_whereami_produces_output_for_populated_context():
    from rich.console import Console

    context = {
        "runtime": {"python": "3.11.0", "cwd": "/tmp"},
        "process": {"pid": 42, "argv": "python -m foo"},
        "frame": {"file": "a.py", "line": 10, "function": "handler"},
        "django": None,
        "celery": None,
        "opentelemetry": None,
        "structlog": None,
    }

    console = Console(record=True, width=120)
    console.print(render_whereami(context))
    output = console.export_text()

    assert "Runtime" in output
    assert "3.11.0" in output
    assert "Process" in output
    assert "handler" in output


def test_render_whereami_flattens_nested_request_dict():
    from rich.console import Console

    context = {
        "runtime": {"python": "3.11.0"},
        "django": {
            "DEBUG": True,
            "request": {"method": "POST", "path": "/invoices/"},
        },
    }

    console = Console(record=True, width=120)
    console.print(render_whereami(context))
    output = console.export_text()

    assert "request.method" in output
    assert "POST" in output
    assert "request.path" in output


def test_do_whereami_prints_runtime_and_frame(capsys, RichPdb, no_frameworks):
    RichPdb().do_whereami("")

    output = capsys.readouterr().out
    assert "Runtime" in output
    assert "Frame" in output
    assert f"{sys.version_info.major}.{sys.version_info.minor}" in output


def test_do_whereami_skips_absent_framework_sections(capsys, RichPdb, no_frameworks):
    RichPdb().do_whereami("")

    output = capsys.readouterr().out
    assert "Django" not in output
    assert "Celery" not in output
    assert "OpenTelemetry" not in output
    assert "Structlog" not in output


def test_collect_context_reports_structlog_when_bound(monkeypatch):
    structlog = pytest.importorskip("structlog")

    for name in ("django", "celery", "opentelemetry"):
        monkeypatch.setitem(sys.modules, name, None)

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(user_id=42, tenant="acme")

    try:
        context = collect_context(inspect.currentframe())
    finally:
        structlog.contextvars.clear_contextvars()

    assert context["structlog"] == {"user_id": 42, "tenant": "acme"}


def test_ipython_whereami_magic_registers_and_sets_last_whereami():
    pytest.importorskip("IPython")
    from IPython.testing.globalipapp import get_ipython

    from pdbr.ipython_magics import register_pdbr_ipython_magics

    ip = get_ipython()
    assert ip is not None
    assert register_pdbr_ipython_magics(ip) is True

    ip.run_line_magic("whereami", "")

    assert "_last_whereami" in ip.user_ns
    snapshot = ip.user_ns["_last_whereami"]
    assert snapshot["runtime"]["python"].startswith(
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    assert snapshot["frame"] is not None
