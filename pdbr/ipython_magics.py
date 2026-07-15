from pdbr.diff_command import (
    compute_diff,
    render_diff,
    split_two_expressions,
)
from pdbr.logging import CLEAR_SENTINEL, query_logs
from pdbr.whereami import collect_context, render_whereami

_registered = False


def register_pdbr_ipython_magics(ipython=None):
    """Register ``%log`` / ``%whereami`` / ``%diff`` on the active IPython
    shell; returns ``False`` when IPython is unavailable, safe to call
    repeatedly."""
    global _registered

    try:
        from IPython.core.magic import Magics, line_magic, magics_class
    except ImportError:
        return False

    if ipython is None:
        try:
            from IPython import get_ipython
        except ImportError:
            return False
        ipython = get_ipython()

    if ipython is None:
        return False

    if _registered:
        return True

    @magics_class
    class PdbrLogMagics(Magics):
        @line_magic("log")
        def log(self, line):
            from rich.console import Console

            try:
                result = query_logs(line)
            except ValueError as err:
                print("*** " + str(err))
                return

            if result is CLEAR_SENTINEL:
                return

            records, renderable = result
            self.shell.user_ns["_last_log"] = records
            Console().print(renderable)

        @line_magic("whereami")
        def whereami(self, line):
            import sys

            from rich.console import Console

            frame = sys._getframe(1)
            context = collect_context(frame)
            self.shell.user_ns["_last_whereami"] = context
            Console().print(render_whereami(context))

        @line_magic("diff")
        def diff(self, line):
            from rich.console import Console

            parsed = split_two_expressions(line or "")
            if parsed is None:
                print("*** Usage: %diff <expr1> <expr2>")
                return
            expr_a, expr_b = parsed
            user_ns = self.shell.user_ns
            try:
                left = eval(expr_a, self.shell.user_global_ns, user_ns)
                right = eval(expr_b, self.shell.user_global_ns, user_ns)
            except Exception as err:
                print(f"*** {type(err).__name__}: {err}")
                return

            changes = compute_diff(left, right)
            user_ns["_last_diff"] = changes
            Console().print(
                render_diff(changes, before_label=expr_a, after_label=expr_b)
            )

    ipython.register_magics(PdbrLogMagics)
    _registered = True
    return True


def load_ipython_extension(ipython):
    register_pdbr_ipython_magics(ipython)
