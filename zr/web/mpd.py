import asyncio

from aiohttp.web import HTTPNotFound

from .lib.resources import Resource, DispatchMixin
from .lib.views import RESTView


class GetView(RESTView):
    methods = {'get'}

    @asyncio.coroutine
    def get(self):
        return (yield from self.resource.get())


class MPDBase(Resource):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.mpd = self.app['mpd']


class MPD(DispatchMixin, MPDBase):
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


class MPDSong(DispatchMixin, MPDBase):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.id = int(name)

    @asyncio.coroutine
    def get(self):
        playlist = yield from self.mpd.playlist.list()

        for song in playlist:
            if song['id'] == self.id:
                return song
        else:
            return None

    @asyncio.coroutine
    def play(self):
        return (yield from self.mpd.playlist.play(self.id))


class MPDSongView(RESTView):
    methods = {'get', 'put'}

    @asyncio.coroutine
    def get(self):
        song = yield from self.resource.get()

        if song:
            return song
        else:
            raise HTTPNotFound

    @asyncio.coroutine
    def put(self):
        return (yield from self.resource.play())


def includeme(app):
    app.bind_view(MPDBase, GetView)
    app.add_child(app.root_class, 'mpd', MPD)
    app.add_child(MPD, 'playlist', MPDPlaylist)
    app.bind_view(MPDSong, MPDSongView)
