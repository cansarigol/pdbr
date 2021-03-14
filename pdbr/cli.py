import sys
from telnetlib import Telnet

from rich.file_proxy import FileProxy

from pdbr.utils import pdbr_cls


def shell():
    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        from IPython.terminal.ipapp import TerminalIPythonApp
        from traitlets import Type
    except ModuleNotFoundError as error:
        raise type(error)(
            "In order to use pdbr shell, install IPython with pdbr[ipython]"
        ) from error

    class PdbrTerminalInteractiveShell(TerminalInteractiveShell):
        @property
        def debugger_cls(self):
            return pdbr_cls(return_instance=False)

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


def telnet():
    pdb_cls = pdbr_cls()
    if len(sys.argv) < 3:
        pdb_cls.error("Usage : pdbr_telnet hostname port")
        sys.exit()

    class MyTelnet(Telnet):
        def fill_rawq(self):
            """
            exactly the same with Telnet.fill_rawq,
            buffer size is just changed from 50 to 1024.
            """
            if self.irawq >= len(self.rawq):
                self.rawq = b""
                self.irawq = 0
            buf = self.sock.recv(1024)
            self.msg("recv %r", buf)
            self.eof = not buf
            self.rawq = self.rawq + buf

    console = pdbr_cls().console
    sys.stdout = FileProxy(console, sys.stdout)
    sys.stderr = FileProxy(console, sys.stderr)
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        with MyTelnet(host, port) as tn:
            tn.interact()
    except BaseException as e:
        pdb_cls.error(e)
        sys.exit()
