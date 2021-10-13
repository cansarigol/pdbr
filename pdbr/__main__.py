import os
import pdb
import sys

from .utils import _pdbr_cls, _rdbr_cls

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"

RichPdb = _pdbr_cls(return_instance=False, show_layouts=False)


def set_trace(*, header=None, context=None, show_layouts=False):
    pdb_cls = _pdbr_cls(context=context, show_layouts=show_layouts)
    if header is not None:
        pdb_cls.message(header)
    pdb_cls.set_trace(sys._getframe().f_back)


def run(statement, globals=None, locals=None):
    RichPdb().run(statement, globals, locals)


def post_mortem(traceback=None, value=None):
    _, sys_value, sys_traceback = sys.exc_info()
    value = value or sys_value
    traceback = traceback or sys_traceback

    if traceback is None:
        raise ValueError(
            "A valid traceback must be passed if no exception is being handled"
        )

    p = RichPdb()
    p.reset()
    if value:
        p.error(value)
    p.interaction(None, traceback)


def pm():
    post_mortem(sys.last_traceback)


def celery_set_trace(frame=None):
    pdb_cls = _rdbr_cls()
    if frame is None:
        frame = sys._getframe().f_back
    return pdb_cls.set_trace(frame)


if __name__ == "__main__":
    pdb.Pdb = RichPdb
    pdb.main()
