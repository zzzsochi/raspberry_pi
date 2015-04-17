import asyncio

from aiohttp.web import HTTPNotFound

from .lib.resources import Root as BaseRoot
from .lib.static import StaticResource, StaticView

from .mpd import MPD


class Root(BaseRoot):
    path = 'zr/web/static/index.html'

    @asyncio.coroutine
    def __getchild__(self, name):
        if name == 'mpd':
            return MPD(self, name)
        elif name == 'static':
            return StaticResource(self, name, 'zr/web/static/')
        else:
            raise HTTPNotFound()


def includeme(app):
    app.set_root_factory(Root)
    app.setup_resource(Root, StaticView)

    app.include('zr.web.lib.static')
    app.include('zr.web.mpd')
