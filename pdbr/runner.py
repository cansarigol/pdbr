import unittest

from django.test.runner import DebugSQLTextTestResult, DiscoverRunner

from pdbr.__main__ import RichPdb, post_mortem


class PDBRDebugResult(unittest.TextTestResult):
    _pdbr = RichPdb()

    def addError(self, test, err):
        super().addError(test, err)
        self._print(test, err)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._print(test, err)

    def _print(self, test, err):
        self.buffer = False
        self._pdbr.message(f"\n{test}")
        self._pdbr.error("%s: %s", err[0].__name__, err[1])
        post_mortem(err[2])


class PdbrDiscoverRunner(DiscoverRunner):
    def get_resultclass(self):
        if self.debug_sql:
            return DebugSQLTextTestResult
        return PDBRDebugResult
