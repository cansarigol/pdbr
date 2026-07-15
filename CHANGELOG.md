# Changelog

All notable changes to `pdbr` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.8] - Unreleased

### Added

- **`log` command** — Rich-rendered ring buffer of stdlib `logging` records
  captured via an auto-installed root handler, with filters and `[pdbr.log]`
  config. `structlog` (stdlib bridge) is captured for free.
- **`whereami` command** — one-shot snapshot of runtime, process, current
  frame, and auto-detected Django / Celery / OpenTelemetry / Structlog
  context. Optional sections fail independently.
- **`diff` command** — semantic diff of two expressions with normalization
  for `dict`/`list`/`set`/dataclass/Django `Model`/Pydantic/`attrs`, plus
  cycle and depth guards. Type changes are surfaced separately.
- **IPython magics** — `%log`, `%whereami`, `%diff` for use outside a
  breakpoint, with `_last_log` / `_last_whereami` / `_last_diff` exposed
  in the IPython namespace.
- **`traceback_show_locals` config option** (default `False`) — set to
  `True` for Rich's per-frame locals dump; kept off by default because
  locals may contain tokens, PII, or secrets.

### Changed

- **Dropped Python 3.7 / 3.8 / 3.9.** Minimum is now 3.10, letting the
  codebase use PEP 604 unions and standard-collection subscripting.
- **Python 3.13+ compatibility.** `telnetlib` was removed from the stdlib
  in 3.13 (PEP 594). `pdbr_telnet` now imports `telnetlib` lazily and
  points users to the `pdbr[telnet]` extra (backed by `telnetlib3`) when
  the module is missing. The `pdbr` command itself works on 3.13+ without
  the extra.
- `use_traceback` default is now an explicit `True` fallback in
  `getboolean` — same effective behavior as `0.9.7`, cleaner code path.
- `set_traceback(theme)` gained a `show_locals` parameter wired to the
  new `traceback_show_locals` config key.

### Removed

- `noxfile.py`, `runtests.py`, and `tests/tests_django/` — the Django
  version matrix tested two trivial smoke assertions across EOL Django
  releases (3.2, 4.2). CI now runs pytest directly with an updated
  Python matrix (`3.10`–`3.14`).

## [0.9.7] - baseline

Everything up to and including tag `v0.9.7`. See the git log for
per-commit history prior to `0.9.8`.
