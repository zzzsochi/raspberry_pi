import os
import asyncio

from aiohttp.web import Response
from aiotraversal.resources import Root
from aiotraversal.views import MethodsView


class RootView(MethodsView):
    methods = {'get'}

    @asyncio.coroutine
    def get(self):
        static = yield from self.resource['static']

        if not self.request.tail:
            info = static.get('index.html')
        else:
            info = static.get(os.path.join(*self.request.tail))

        return Response(
            body=info.data,
            headers={'Content-Type': info.content_type},
        )


def includeme(app):
    app.include('aiotraversal.resources')
    app.include('aiotraversal.static')

    app.bind_view(Root, RootView)
    app.bind_view(Root, RootView, tail='favicon.ico')

    app.add_static(Root, 'static', 'zr/web/static/')

    app.include('.mpd')
    app.include('.settings')
