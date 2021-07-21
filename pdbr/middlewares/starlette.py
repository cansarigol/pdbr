from starlette.middleware.errors import ServerErrorMiddleware

from pdbr._cm import apdbr_context


class PdbrMiddleware(ServerErrorMiddleware):
    async def __call__(self, scope, receive, send) -> None:
        async with apdbr_context(suppress_exc=False, debug=self.debug):
            await super().__call__(scope, receive, send)
