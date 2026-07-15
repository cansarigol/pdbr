import os
import sys

from rich import box
from rich.console import Group
from rich.table import Table
from rich.text import Text

_MAX_ARGV_ITEMS = 4
_MAX_REQUEST_WALK = 8

_SECTIONS = (
    ("runtime", "Runtime"),
    ("process", "Process"),
    ("frame", "Frame"),
    ("django", "Django"),
    ("celery", "Celery"),
    ("opentelemetry", "OpenTelemetry"),
    ("structlog", "Structlog context"),
)


def collect_context(frame=None):
    """Snapshot runtime, process, frame, and optional framework state."""
    return {
        "runtime": _collect_runtime(),
        "process": _collect_process(),
        "frame": _collect_frame(frame),
        "django": _collect_django(frame),
        "celery": _collect_celery(),
        "opentelemetry": _collect_opentelemetry(),
        "structlog": _collect_structlog(),
    }


def render_whereami(context):
    tables = [
        _render_section(title, context[key])
        for key, title in _SECTIONS
        if context.get(key)
    ]
    if not tables:
        return Text("(no context available)")
    return Group(*tables)


def _render_section(title, info):
    table = Table(title=title, box=box.MINIMAL, show_header=False, title_style="bold")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    for key, value in _flatten(info):
        table.add_row(key, str(value))
    return table


def _flatten(info, prefix=""):
    for key, value in info.items():
        composed = f"{prefix}{key}"
        if isinstance(value, dict):
            yield from _flatten(value, f"{composed}.")
        else:
            yield composed, value


def _collect_runtime():
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}",
        "executable": sys.executable,
        "venv": sys.prefix if sys.prefix != sys.base_prefix else "(system)",
        "cwd": os.getcwd(),
    }


def _collect_process():
    argv = sys.argv[:_MAX_ARGV_ITEMS]
    display = " ".join(argv)
    if len(sys.argv) > _MAX_ARGV_ITEMS:
        display += " ..."
    return {"pid": os.getpid(), "argv": display}


def _collect_frame(frame):
    if frame is None:
        return None
    code = frame.f_code
    return {
        "file": code.co_filename,
        "line": frame.f_lineno,
        "function": getattr(code, "co_qualname", code.co_name),
    }


def _collect_django(frame):
    try:
        from django.conf import settings
    except ImportError:
        return None

    info = {}
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if settings_module:
        info["settings_module"] = settings_module

    try:
        info["DEBUG"] = settings.DEBUG
    except Exception:
        return info or None

    try:
        from django.db import transaction

        connection = transaction.get_connection()
        info["db_alias"] = connection.alias
        info["in_atomic_block"] = connection.in_atomic_block
    except Exception:
        pass

    request_info = _extract_request(frame)
    if request_info:
        info["request"] = request_info

    return info


def _extract_request(frame):
    candidate = _walk_frame_locals_for(frame, "request")
    if candidate is None:
        return None

    method = getattr(candidate, "method", None)
    path = getattr(candidate, "path", None) or getattr(candidate, "path_info", None)
    if not method or not path:
        return None

    user = getattr(candidate, "user", None)
    return {
        "method": method,
        "path": path,
        "user": str(user) if user is not None else "(anonymous)",
    }


def _walk_frame_locals_for(frame, name):
    current = frame
    depth = 0
    while current is not None and depth < _MAX_REQUEST_WALK:
        found = current.f_locals.get(name)
        if found is not None:
            return found
        current = current.f_back
        depth += 1
    return None


def _collect_celery():
    try:
        from celery import current_task
    except ImportError:
        return None

    try:
        task = current_task._get_current_object()
    except Exception:
        task = current_task

    if task is None:
        return None

    request = getattr(task, "request", None)
    task_id = getattr(request, "id", None) if request is not None else None
    name = getattr(task, "name", None)
    if not name and not task_id:
        return None

    return {"name": name, "id": task_id}


def _collect_opentelemetry():
    try:
        from opentelemetry import trace
    except ImportError:
        return None

    try:
        span = trace.get_current_span()
        context = span.get_span_context()
    except Exception:
        return None

    if not context.is_valid:
        return None

    return {
        "trace_id": format(context.trace_id, "032x"),
        "span_id": format(context.span_id, "016x"),
    }


def _collect_structlog():
    try:
        from structlog.contextvars import get_contextvars
    except ImportError:
        return None

    try:
        bound = get_contextvars()
    except Exception:
        return None

    return bound or None
