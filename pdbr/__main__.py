import configparser
import os
import sys

from pdbr._pdbr import RichPdb

from .utils import set_history_file, set_traceback

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def _pdbr():
    import pdb

    style, theme = _read_config()

    RichPdb._style = style
    RichPdb._theme = theme
    pdb.Pdb = RichPdb
    return pdb


def _rdbr():
    pdb_klass = _pdbr().Pdb
    try:
        from celery.contrib import rdb
    except ModuleNotFoundError as error:
        raise type(error)("In order to install celery, use pdbr[celery]") from error

    rdb.Pdb = pdb_klass
    return rdb


def set_trace(*, header=None):
    pdb_klass = _pdbr().Pdb()
    if header is not None:
        pdb_klass.message(header)
    pdb_klass.set_trace(sys._getframe().f_back)


def run(statement, globals=None, locals=None):
    _pdbr().run(statement, globals, locals)


def post_mortem(t=None):
    _pdbr().post_mortem(t)


def pm():
    _pdbr().pm()


def celery_set_trace(frame=None):
    rdb_klass = _rdbr().Rdb()
    if frame is None:
        frame = getattr(sys, "_getframe")().f_back
    return rdb_klass.set_trace(frame)


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
