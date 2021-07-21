import sys

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

from pdbr.__main__ import post_mortem


class PdbrMiddleware:
    def __init__(self, get_response):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):  # noqa: F841
        post_mortem(sys.exc_info()[2])
