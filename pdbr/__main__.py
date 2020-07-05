import configparser
import os
import sys

from pdbr._pdbr import RichPdb

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"
style = None
theme = None


def set_trace(*, header=None, context=None):
    read_config()
    pdb = RichPdb(style=style, theme=theme)
    if header is not None:
        pdb.message(header)
    pdb.set_trace(sys._getframe().f_back)


def run(statement, globals=None, locals=None):
    read_config()
    RichPdb(style=style, theme=theme).run(statement, globals, locals)


def read_config():
    global style
    global theme

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
                from rich.traceback import install

                install(theme=theme)


if __name__ == "__main__":
    import pdb

    pdb.Pdb = RichPdb
    pdb.main()


read_config()
