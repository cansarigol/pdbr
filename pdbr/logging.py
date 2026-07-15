import logging
import shlex
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich import box
from rich.table import Table
from rich.text import Text

_STANDARD_LOGRECORD_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }
)


@dataclass(frozen=True)
class CapturedLog:
    ts: datetime
    level: int
    logger: str
    message: str
    exc_info: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def _repr_pretty_(self, printer, cycle):
        printer.text(
            "<CapturedLog {level} {logger}: {message}>".format(
                level=logging.getLevelName(self.level),
                logger=self.logger,
                message=self.message,
            )
        )


class RingHandler(logging.Handler):
    def __init__(self, buffer_size):
        super().__init__()
        self.buffer = deque(maxlen=buffer_size)
        # Remembered so uninstall can restore whatever root's level was before
        # install bumped it. None means install left root untouched.
        self.saved_root_level = None

    def emit(self, record):
        try:
            message = record.getMessage()
        except Exception:
            # Formatting failures shouldn't drop the record; fall back to raw msg.
            message = str(record.msg)

        exc_text = None
        if record.exc_info:
            try:
                exc_text = logging.Formatter().formatException(record.exc_info)
            except Exception:
                exc_text = None

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOGRECORD_ATTRS and not key.startswith("_")
        }

        self.buffer.append(
            CapturedLog(
                ts=datetime.fromtimestamp(record.created),
                level=record.levelno,
                logger=record.name,
                message=message,
                exc_info=exc_text,
                extra=extra,
            )
        )


def _find_ring_handler(logger):
    return next(
        (h for h in logger.handlers if isinstance(h, RingHandler)),
        None,
    )


def install_log_capture(buffer_size=500, level=logging.WARNING, enabled=True):
    """Attach a ring-buffer handler to the root logger; idempotent. Raising
    ``level`` below root's threshold lifts root too, so every other handler
    on the tree will start seeing those records — see README."""
    root = logging.getLogger()
    if not enabled or _find_ring_handler(root) is not None:
        return

    handler = RingHandler(buffer_size)
    handler.setLevel(level)
    root.addHandler(handler)

    if root.getEffectiveLevel() > level:
        handler.saved_root_level = root.level
        root.setLevel(level)


def uninstall_log_capture():
    root = logging.getLogger()
    handler = _find_ring_handler(root)
    if handler is None:
        return

    root.removeHandler(handler)
    if handler.saved_root_level is not None:
        root.setLevel(handler.saved_root_level)


def get_log_buffer():
    """Return the current ring buffer, or an empty deque when capture is off."""
    handler = _find_ring_handler(logging.getLogger())
    return handler.buffer if handler is not None else deque()


CLEAR_SENTINEL = object()


def query_logs(arg):
    """Return ``CLEAR_SENTINEL`` when ``arg`` is ``clear``, otherwise a
    ``(records, renderable)`` tuple; raises ``ValueError`` on bad args."""
    tokens = shlex.split(arg or "")
    if tokens and tokens[0] == "clear":
        get_log_buffer().clear()
        return CLEAR_SENTINEL

    count, level_min, contains, logger_substr = _parse_log_args(tokens)
    records = _filter_log_records(get_log_buffer(), level_min, contains, logger_substr)
    limited = records[-count:]
    return limited, _render_log_table(limited)


def _parse_log_args(tokens):
    count = 20
    level_min = None
    contains = None
    logger_substr = None

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--level", "--contains", "--logger"):
            if index + 1 >= len(tokens):
                raise ValueError("Missing value for " + token)
            value = tokens[index + 1]
            if token == "--level":
                resolved = getattr(logging, value.upper(), None)
                if not isinstance(resolved, int):
                    raise ValueError("Unknown log level: " + value)
                level_min = resolved
            elif token == "--contains":
                contains = value
            else:
                logger_substr = value
            index += 2
        else:
            try:
                count = int(token)
            except ValueError as parse_err:
                raise ValueError("Unknown argument: " + token) from parse_err
            index += 1

    return count, level_min, contains, logger_substr


def _filter_log_records(buffer, level_min, contains, logger_substr):
    filtered = []
    # Snapshot first so a concurrent emit doesn't raise
    # "deque mutated during iteration" mid-scan.
    for entry in list(buffer):
        if level_min is not None and entry.level < level_min:
            continue
        if contains is not None and contains not in entry.message:
            continue
        if logger_substr is not None and logger_substr not in entry.logger:
            continue
        filtered.append(entry)
    return filtered


_LEVEL_STYLES = {
    logging.DEBUG: "dim",
    logging.INFO: "cyan",
    logging.WARNING: "yellow",
    logging.ERROR: "red",
    logging.CRITICAL: "bold red",
}


def _render_log_table(records):
    if not records:
        return Text("No log records captured.")

    table = Table(title="Captured logs", box=box.MINIMAL)
    table.add_column("Time", style="dim")
    table.add_column("Level")
    table.add_column("Logger", style="cyan")
    table.add_column("Message", style="magenta")
    table.add_column("Extra", style="green")

    for entry in records:
        extra_text = (
            ", ".join(f"{key}={value!r}" for key, value in entry.extra.items())
            if entry.extra
            else ""
        )
        table.add_row(
            entry.ts.strftime("%H:%M:%S.%f")[:-3],
            Text(
                logging.getLevelName(entry.level),
                style=_LEVEL_STYLES.get(entry.level, "white"),
            ),
            entry.logger,
            entry.message,
            extra_text,
        )

    return table
