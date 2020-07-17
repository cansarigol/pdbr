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


def _read_config():
    style = None
    theme = None
    is_history_file_set = False

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
            is_history_file_set = True

    if is_history_file_set is False:
        set_history_file(".pdbr_history")

    return style, theme


if __name__ == "__main__":
    _pdbr().main()
