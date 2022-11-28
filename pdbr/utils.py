import atexit
import configparser
from pathlib import Path

from pdbr._pdbr import rich_pdb_klass

try:
    import readline
except ImportError:
    try:
        from pyreadline3 import Readline

        readline = Readline()
    except ModuleNotFoundError:
        readline = None
except AttributeError:
    readline = None


def set_history_file(history_file):
    """
    This is just for Pdb,
    For Ipython, look at RichPdb.pt_init
    """
    if readline is None:
        return
    try:
        readline.read_history_file(history_file)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    except OSError:
        pass

    atexit.register(readline.write_history_file, history_file)


def set_traceback(theme):
    from rich.traceback import install

    install(theme=theme)


def read_config():
    style = None
    theme = None
    store_history = ".pdbr_history"

    config = configparser.ConfigParser()
    config.sections()

    setup_filename = "setup.cfg"
    global_config_path = Path.home() / ".config" / "pdbr" / setup_filename
    cwd_config_path = Path.cwd() / setup_filename
    config_path = cwd_config_path.exists() and cwd_config_path or global_config_path

    config.read(config_path)
    if "pdbr" in config:
        if "style" in config["pdbr"]:
            style = config["pdbr"]["style"]
        if "theme" in config["pdbr"]:
            theme = config["pdbr"]["theme"]
        if "use_traceback" in config["pdbr"]:
            if config["pdbr"]["use_traceback"].lower() == "true":
                set_traceback(theme)
        if "store_history" in config["pdbr"]:
            store_history = config["pdbr"]["store_history"]

    history_file = str(Path.home() / store_history)
    set_history_file(history_file)
    ipython_history_file = f"{history_file}_ipython"

    return style, theme, history_file, ipython_history_file


def debugger_cls(klass=None, context=None, is_celery=False, show_layouts=True):
    if klass is None:
        try:
            from IPython.terminal.debugger import TerminalPdb

            klass = TerminalPdb
        except ImportError:
            from pdb import Pdb

            klass = Pdb

    RichPdb = rich_pdb_klass(
        klass, context=context, is_celery=is_celery, show_layouts=show_layouts
    )
    style, theme, history_file, ipython_history_file = read_config()
    RichPdb._style = style
    RichPdb._theme = theme
    RichPdb._history_file = history_file
    RichPdb._ipython_history_file = ipython_history_file

    return RichPdb


def _pdbr_cls(context=None, return_instance=True, show_layouts=True):
    klass = debugger_cls(context=context, show_layouts=show_layouts)
    if return_instance:
        return klass()
    return klass


def _rdbr_cls(return_instance=True):
    try:
        from celery.contrib import rdb

        rdb.BANNER = """\
{self.ident}: Type `pdbr_telnet {self.host} {self.port}` to connect

{self.ident}: Waiting for client...
"""
    except ModuleNotFoundError as error:
        raise type(error)("In order to install celery, use pdbr[celery]") from error

    klass = debugger_cls(klass=rdb.Rdb, is_celery=True, show_layouts=False)
    if return_instance:
        return klass()
    return klass
