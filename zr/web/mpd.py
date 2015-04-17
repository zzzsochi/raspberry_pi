import json
import asyncio

from aiohttp.web import Response
from aiohttp.web import HTTPNotFound

from .lib.resources import Resource
from .lib.views import View


def jsonify(coro):
    @asyncio.coroutine
    def wrapper(self):
        data = yield from coro(self)
        return Response(body=json.dumps(data).encode('utf8'))

    return wrapper


class JSONView(View):
    @jsonify
    def __call__(self):
        return (yield from self.resource.get())


class MPDBase(Resource):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.mpd = self.app['mpd']


class MPD(MPDBase):
    @asyncio.coroutine
    def __getchild__(self, name):
        if name == 'playlist':
            return MPDPlaylist(self, name)
        else:
            raise HTTPNotFound()

    @asyncio.coroutine
    def get(self):
        return (yield from self.mpd.get_status())


class MPDPlaylist(MPDBase):
    @asyncio.coroutine
    def get(self):
        return (yield from self.mpd.playlist.list())

    @asyncio.coroutine
    def __getchild__(self, name):
        return MPDSong(self, name)


class MPDSong(MPDBase):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.id = int(name)

    @asyncio.coroutine
    def play(self):
        return (yield from self.mpd.playlist.play(self.id))


class MPDSongView(JSONView):
    @jsonify
    def __call__(self):
        return (yield from self.resource.play())


def includeme(app):
    app.setup_resource(MPDBase, JSONView)
    app.setup_resource(MPDSong, MPDSongView)
