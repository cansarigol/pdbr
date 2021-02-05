import configparser
import os
import sys

from pdbr._pdbr import rich_pdb_klass

from .utils import set_history_file, set_traceback

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def debugger_cls():
    try:
        from IPython.terminal.debugger import TerminalPdb

        return TerminalPdb
    except BaseException:
        from pdb import Pdb

        return Pdb


def __set_style_theme(RichPdb):
    style, theme = _read_config()
    RichPdb._style = style
    RichPdb._theme = theme
    return RichPdb()


def _pdbr():
    return __set_style_theme(rich_pdb_klass(debugger_cls()))


def _rdbr():
    try:
        from celery.contrib import rdb
    except ModuleNotFoundError as error:
        raise type(error)("In order to install celery, use pdbr[celery]") from error

    return __set_style_theme(rich_pdb_klass(rdb.Rdb, is_celery=True))


def set_trace(*, header=None):
    pdb_cls = _pdbr()
    if header is not None:
        pdb_cls.message(header)
    pdb_cls.set_trace(sys._getframe().f_back)


def run(statement, globals=None, locals=None):
    _pdbr().run(statement, globals, locals)


def post_mortem(t=None):
    _pdbr().post_mortem(t)


def pm():
    _pdbr().pm()


def celery_set_trace(frame=None):
    pdb_cls = _rdbr()
    if frame is None:
        frame = getattr(sys, "_getframe")().f_back
    return pdb_cls.set_trace(frame)


def _read_config():
    style = None
    theme = None

    config = configparser.ConfigParser()
    config.sections()
    config.read("setup.cfg")
    if "pdbr" in config:
        if "style" in config["pdbr"]:
            style = config["pdbr"]["style"]
        if "theme" in config["pdbr"]:
            theme = config["pdbr"]["theme"]
        if "use_traceback" in config["pdbr"]:
            if config["pdbr"]["use_traceback"].lower() == "true":
                set_traceback(theme)
        if "store_history" in config["pdbr"]:
            set_history_file(config["pdbr"]["store_history"])

    return style, theme


if __name__ == "__main__":
    _pdbr().main()
