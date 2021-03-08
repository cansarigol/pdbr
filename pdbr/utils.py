import configparser

from pdbr._pdbr import rich_pdb_klass


def set_history_file(filename):
    import atexit
    import os
    import readline

    histfile = os.path.join(os.path.expanduser("~"), filename)
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)


def set_traceback(theme):
    from rich.traceback import install

    install(theme=theme)


def read_config():
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


def debugger_cls(klass=None, context=None, is_celery=False):
    if klass is None:
        try:
            from IPython.terminal.debugger import TerminalPdb

            klass = TerminalPdb
        except BaseException:
            from pdb import Pdb

            klass = Pdb

    RichPdb = rich_pdb_klass(klass, context=context, is_celery=is_celery)
    style, theme = read_config()
    RichPdb._style = style
    RichPdb._theme = theme

    return RichPdb


def pdbr_cls(context=None, return_instance=True):
    klass = debugger_cls(context=context)
    if return_instance:
        return klass()
    return klass


def rdbr_cls(return_instance=True):
    try:
        from celery.contrib import rdb
    except ModuleNotFoundError as error:
        raise type(error)("In order to install celery, use pdbr[celery]") from error

    klass = debugger_cls(klass=rdb.Rdb, is_celery=True)
    if return_instance:
        return klass()
    return klass
