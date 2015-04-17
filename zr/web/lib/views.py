import asyncio

from aiohttp.web import Response


class View:
    def __init__(self, resource):
        self.resource = resource
        self.request = self.resource.request

    @asyncio.coroutine
    def __call__(self):
        raise NotImplementedError
        # return Response(body=self.request.path.encode('utf8'))
