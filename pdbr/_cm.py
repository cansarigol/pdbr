from contextlib import ContextDecorator

from pdbr.__main__ import post_mortem


class pdbr_context(ContextDecorator):
    def __init__(self, suppress_exc=True):
        self.suppress_exc = suppress_exc

    def __enter__(self):
        return self

    def __exit__(self, _, exc_value, exc_traceback):
        if exc_traceback:
            post_mortem(exc_traceback, exc_value)
            return self.suppress_exc
        return False
