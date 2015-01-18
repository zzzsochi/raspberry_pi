import asyncio
from aiohttp.web import Application, Response


class Web(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router.add_route('GET', '/', hello)


@asyncio.coroutine
def hello(request):
    return Response(body=b"Hello, world")
