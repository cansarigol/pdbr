import dataclasses
import datetime
import decimal
import pathlib
import uuid
from collections import namedtuple

from rich import box
from rich.table import Table
from rich.text import Text

CHANGED = "changed"
ADDED = "added"
REMOVED = "removed"
TYPE_CHANGED = "type_changed"

DiffEntry = namedtuple("DiffEntry", "kind path old new")

_MISSING = object()

_LEAF_TYPES = (
    str,
    bytes,
    bytearray,
    int,
    float,
    bool,
    type(None),
    complex,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
    uuid.UUID,
    decimal.Decimal,
    pathlib.PurePath,
)

_DEFAULT_MAX_DEPTH = 8
_REPR_MAX = 80


def compute_diff(a, b, max_depth=_DEFAULT_MAX_DEPTH):
    """Return ``list[DiffEntry]`` for structural differences across
    dict/list/set/dataclass/Django Model/Pydantic/attrs, guarded against
    cycles and depth blow-ups."""
    changes = []
    _walk(a, b, path=(), changes=changes, depth=0, max_depth=max_depth, seen=set())
    return changes


def render_diff(changes, before_label="Old", after_label="New"):
    if not changes:
        return Text("(no differences)", style="green")

    table = Table(
        title=f"Diff ({len(changes)} change{'s' if len(changes) != 1 else ''})",
        box=box.MINIMAL,
        title_style="bold",
        show_lines=False,
    )
    table.add_column("Path", style="cyan", no_wrap=True)
    table.add_column(before_label, overflow="fold")
    table.add_column(after_label, overflow="fold")

    for entry in changes:
        table.add_row(*_format_row(entry))

    return table


def _walk(a, b, path, changes, depth, max_depth, seen):
    if depth > max_depth:
        if a != b:
            changes.append(DiffEntry(CHANGED, path, a, b))
        return

    key = (id(a), id(b))
    if key in seen:
        return
    seen.add(key)

    na = _normalize(a)
    nb = _normalize(b)

    both_opaque = na is None and nb is None
    if both_opaque:
        if type(a) is not type(b):
            changes.append(DiffEntry(TYPE_CHANGED, path, a, b))
        elif a != b:
            changes.append(DiffEntry(CHANGED, path, a, b))
        return

    if na is None or nb is None or type(na) is not type(nb):
        changes.append(DiffEntry(TYPE_CHANGED, path, a, b))
        return

    if isinstance(na, dict):
        _walk_dict(na, nb, path, changes, depth, max_depth, seen)
    elif isinstance(na, list):
        _walk_list(na, nb, path, changes, depth, max_depth, seen)
    elif isinstance(na, set):
        _walk_set(na, nb, path, changes)


def _walk_dict(a, b, path, changes, depth, max_depth, seen):
    all_keys = list(a.keys()) + [k for k in b.keys() if k not in a]
    for key in all_keys:
        step = (f".{key}",) if _is_identifier(key) else (f"[{key!r}]",)
        if key not in a:
            changes.append(DiffEntry(ADDED, path + step, _MISSING, b[key]))
        elif key not in b:
            changes.append(DiffEntry(REMOVED, path + step, a[key], _MISSING))
        else:
            _walk(
                a[key],
                b[key],
                path + step,
                changes,
                depth + 1,
                max_depth,
                seen,
            )


def _walk_list(a, b, path, changes, depth, max_depth, seen):
    common = min(len(a), len(b))
    for i in range(common):
        _walk(a[i], b[i], path + (f"[{i}]",), changes, depth + 1, max_depth, seen)
    for i in range(common, len(a)):
        changes.append(DiffEntry(REMOVED, path + (f"[{i}]",), a[i], _MISSING))
    for i in range(common, len(b)):
        changes.append(DiffEntry(ADDED, path + (f"[{i}]",), _MISSING, b[i]))


def _walk_set(a, b, path, changes):
    for elem in sorted(a - b, key=repr):
        changes.append(
            DiffEntry(REMOVED, path + (f"{{{_short_repr(elem)}}}",), elem, _MISSING)
        )
    for elem in sorted(b - a, key=repr):
        changes.append(
            DiffEntry(ADDED, path + (f"{{{_short_repr(elem)}}}",), _MISSING, elem)
        )


def _normalize(obj):
    """Return dict/list/set for containers, None for opaque/leaf."""
    if isinstance(obj, _LEAF_TYPES):
        return None
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, (list, tuple)):
        return list(obj)
    if isinstance(obj, (set, frozenset)):
        return set(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            field.name: getattr(obj, field.name) for field in dataclasses.fields(obj)
        }

    django_dict = _try_django_model(obj)
    if django_dict is not None:
        return django_dict

    pydantic_dict = _try_pydantic(obj)
    if pydantic_dict is not None:
        return pydantic_dict

    attrs_dict = _try_attrs(obj)
    if attrs_dict is not None:
        return attrs_dict

    return _fallback_object_dict(obj)


def _try_django_model(obj):
    try:
        from django.db.models import Model
    except ImportError:
        return None
    if not isinstance(obj, Model):
        return None
    result = {}
    for field in obj._meta.fields:
        if field.is_relation:
            result[field.attname] = getattr(obj, field.attname)
        else:
            result[field.name] = getattr(obj, field.name)
    return result


def _try_pydantic(obj):
    dump = getattr(obj, "model_dump", None)
    if callable(dump) and hasattr(obj, "model_fields"):
        try:
            result = dump()
        except Exception:
            return None
        return result if isinstance(result, dict) else None

    if hasattr(obj, "__fields__"):
        legacy_dump = getattr(obj, "dict", None)
        if callable(legacy_dump):
            try:
                result = legacy_dump()
            except Exception:
                return None
            return result if isinstance(result, dict) else None
    return None


def _try_attrs(obj):
    try:
        import attr
    except ImportError:
        return None
    if not attr.has(type(obj)):
        return None
    try:
        return attr.asdict(obj, recurse=False)
    except Exception:
        return None


def _fallback_object_dict(obj):
    try:
        raw = vars(obj)
    except TypeError:
        return None
    return {k: v for k, v in raw.items() if not k.startswith("__")}


def _is_identifier(key):
    return isinstance(key, str) and key.isidentifier()


def _format_row(entry):
    path = _format_path(entry.path)
    if entry.kind == CHANGED:
        return (
            path,
            Text(_short_repr(entry.old), style="yellow"),
            Text(_short_repr(entry.new), style="yellow"),
        )
    if entry.kind == ADDED:
        return (
            path,
            Text("(missing)", style="dim"),
            Text(_short_repr(entry.new), style="green"),
        )
    if entry.kind == REMOVED:
        return (
            path,
            Text(_short_repr(entry.old), style="red"),
            Text("(removed)", style="dim"),
        )
    if entry.kind == TYPE_CHANGED:
        return (
            path,
            Text(
                f"{_short_repr(entry.old)} <{type(entry.old).__name__}>",
                style="magenta",
            ),
            Text(
                f"{_short_repr(entry.new)} <{type(entry.new).__name__}>",
                style="magenta",
            ),
        )
    return (path, _short_repr(entry.old), _short_repr(entry.new))


def _format_path(path):
    joined = "".join(path)
    return joined.lstrip(".") or "<root>"


def _short_repr(value):
    if value is _MISSING:
        return ""
    text = repr(value)
    if len(text) > _REPR_MAX:
        return text[: _REPR_MAX - 1] + "…"
    return text


def split_two_expressions(text):
    """Split into ``(left, right)`` at the first top-level whitespace,
    respecting brackets and quotes; ``None`` if two non-empty parts cannot
    be extracted."""
    depth = 0
    in_string = None
    for i, ch in enumerate(text):
        if in_string:
            if ch == in_string and text[i - 1] != "\\":
                in_string = None
            continue
        if ch in ('"', "'"):
            in_string = ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch.isspace() and depth == 0:
            left = text[:i].strip()
            right = text[i + 1 :].strip()
            if left and right:
                return left, right
    return None
