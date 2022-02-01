import sys
from telnetlib import Telnet

from rich.file_proxy import FileProxy

from pdbr.helpers import run_ipython_shell


def shell():
    import getopt

    _, args = getopt.getopt(sys.argv[1:], "mhc:", ["command="])

    if not args:
        run_ipython_shell()
    else:
        from pdbr.__main__ import main

        main()


def telnet():
    from pdbr.__main__ import RichPdb

    pdb_cls = RichPdb()
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

    console = pdb_cls.console
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
