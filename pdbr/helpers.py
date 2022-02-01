import sys

from pdbr.__main__ import RichPdb


def run_ipython_shell():
    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        from IPython.terminal.ipapp import TerminalIPythonApp
        from prompt_toolkit.history import FileHistory
        from traitlets import Type

        TerminalInteractiveShell.simple_prompt = False
    except ModuleNotFoundError as error:
        raise type(error)(
            "In order to use pdbr shell, install IPython with pdbr[ipython]"
        ) from error

    class PdbrTerminalInteractiveShell(TerminalInteractiveShell):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            if RichPdb._ipython_history_file:
                self.debugger_history = FileHistory(RichPdb._ipython_history_file)

        @property
        def debugger_cls(self):
            return RichPdb

    class PdbrTerminalIPythonApp(TerminalIPythonApp):
        interactive_shell_class = Type(
            klass=object,  # use default_value otherwise which only allow subclasses.
            default_value=PdbrTerminalInteractiveShell,
            help=(
                "Class to use to instantiate the TerminalInteractiveShell object. "
                "Useful for custom Frontends"
            ),
        ).tag(config=True)

    app = PdbrTerminalIPythonApp.instance()
    app.initialize()
    sys.exit(app.start())
