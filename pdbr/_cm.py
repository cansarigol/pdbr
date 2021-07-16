from contextlib import ContextDecorator
from functools import wraps

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


class AsyncContextDecorator(ContextDecorator):
    def __call__(self, func):
        @wraps(func)
        async def inner(*args, **kwds):
            async with self._recreate_cm():
                return await func(*args, **kwds)

        return inner


class apdbr_context(AsyncContextDecorator):
    def __init__(self, suppress_exc=True):
        self.suppress_exc = suppress_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, _, exc_value, exc_traceback):
        if exc_traceback:
            post_mortem(exc_traceback, exc_value)
            return self.suppress_exc
        return False
