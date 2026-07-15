from pdbr.__main__ import RichPdb, celery_set_trace, pm, post_mortem, run, set_trace
from pdbr._cm import apdbr_context, pdbr_context
from pdbr.diff_command import DiffEntry, compute_diff, render_diff
from pdbr.ipython_magics import (
    load_ipython_extension,
    register_pdbr_ipython_magics,
)
from pdbr.logging import (
    CapturedLog,
    get_log_buffer,
    install_log_capture,
    uninstall_log_capture,
)
from pdbr.whereami import collect_context, render_whereami

register_pdbr_ipython_magics()

__all__ = [
    "set_trace",
    "run",
    "pm",
    "post_mortem",
    "celery_set_trace",
    "RichPdb",
    "pdbr_context",
    "apdbr_context",
    "install_log_capture",
    "uninstall_log_capture",
    "get_log_buffer",
    "CapturedLog",
    "collect_context",
    "render_whereami",
    "compute_diff",
    "render_diff",
    "DiffEntry",
    "register_pdbr_ipython_magics",
    "load_ipython_extension",
]
