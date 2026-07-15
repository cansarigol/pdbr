# Contributing to pdbr

Thanks for helping improve `pdbr`. This document lists the minimum you
need to know to get a change merged.

## Prerequisites

- Python **3.10+** (Python 3.7 / 3.8 / 3.9 are no longer supported).
- [Poetry](https://python-poetry.org/) for dependency management.

## One-time setup

```bash
git clone https://github.com/cansarigol/pdbr.git
cd pdbr
make install
```

`make install` runs `poetry install --with dev` and wires up
`pre-commit` so lint / format checks fire on every commit. The
project ships a `poetry.toml` that pins `virtualenvs.in-project = true`,
so Poetry creates `.venv/` alongside the source tree — no global
configuration needed.

## Development loop

| Task | Command |
| --- | --- |
| Run the tests | `make test` |
| Lint + format all files | `make lint` |

`make lint` is what CI runs — it executes every `pre-commit` hook
(ruff, black, vulture, whitespace / merge-conflict / TOML checks) on
the whole tree. On `git commit`, the same hooks run automatically on
staged files.

Coverage on touched files while iterating:

```bash
poetry run pytest --cov=pdbr/<file> --cov-report=term-missing tests/<test_file>
```

## Adding a new feature

- Put user-facing behavior into a dedicated module under `pdbr/`
  (`pdbr/logging.py`, `pdbr/diff_command.py`, etc.).
- Add a matching test file under `tests/` (`test_<feature>.py`) and
  keep coverage on the new file at 100 %.
- Re-export public symbols from `pdbr/__init__.py` and mirror them in
  `pdbr.__all__` — the assertion in `tests/test_api.py` will catch any
  drift.
- If the feature has a `(Pdbr)` prompt command, add a `do_<cmd>` method
  on `RichPdb` in `pdbr/_pdbr.py`. A one-line docstring is fine — it
  becomes the help text shown by `(Pdbr) help <cmd>`.
- If the feature has an IPython side, add a `%<cmd>` line magic in
  `pdbr/ipython_magics.py`. Convention: also expose the last result as
  `_last_<cmd>` in the IPython namespace.
- Update `README.md` (new command → new section, updated TOC anchor)
  and add a short bullet to `CHANGELOG.md` under `## [Unreleased]`.

## Reporting bugs

Include the pdbr version, Python version, OS, and the smallest snippet
that reproduces the issue. `pdbr` is a debugger — a copy of the
`(Pdbr) whereami` output at the offending breakpoint is a great start.

## Release checklist (maintainer)

1. Bump the version in `pyproject.toml` (both `[tool.poetry]` and
   `[project]` sections stay in sync).
2. Move `## [Unreleased]` in `CHANGELOG.md` to `## [x.y.z] - YYYY-MM-DD`.
3. Tag the commit `vX.Y.Z` and push — the GitHub release workflow
   publishes to PyPI.
