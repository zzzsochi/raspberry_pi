import asyncio

from aiohttp.web import HTTPNotFound, HTTPBadRequest

from .lib.resources import Resource, DispatchMixin, InitCoroMixin
from .lib.views import RESTView


class MPDBase(Resource):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.mpd = self.app['mpd']


class MPD(DispatchMixin, MPDBase):
    @asyncio.coroutine
    def get(self):
        return (yield from self.mpd.get_status())

    @asyncio.coroutine
    def toggle(self):
            return (yield from self.mpd.toggle())

    @asyncio.coroutine
    def prev(self):
            return (yield from self.mpd.prev())

    @asyncio.coroutine
    def next(self):
            return (yield from self.mpd.next())

    @asyncio.coroutine
    def clear(self):
            return (yield from self.mpd.clear())


class MPDView(RESTView):
    methods = {'get', 'post'}

    @asyncio.coroutine
    def get(self):
        return (yield from self.resource.get())

    @asyncio.coroutine
    def post(self):
        action = (yield from self.request.json()).get('action')

        if action == 'toggle':
            yield from self.resource.toggle()
        elif action == 'prev':
            yield from self.resource.prev()
        elif action == 'next':
            yield from self.resource.next()
        elif action == 'clear':
            yield from self.resource.clear()
        else:
            raise HTTPBadRequest(reason="invalid action")

        return (yield from self.resource.get())


class MPDPlaylist(MPDBase):
    @asyncio.coroutine
    def list(self):
        return (yield from self.mpd.playlist())

    @asyncio.coroutine
    def add(self, url):
        return (yield from self.mpd.add(url))

    @asyncio.coroutine
    def __getchild__(self, name):
        return (yield from MPDSong(self, name))


class MPDPlaylistView(RESTView):
    methods = {'get', 'post'}

    @asyncio.coroutine
    def get(self):
        return (yield from self.resource.list())

    @asyncio.coroutine
    def post(self):
        data = yield from self.request.json()

        if 'file' not in data:
            raise HTTPBadRequest(reason="file not exist in request")

        file = data['file']

        if not isinstance(file, str):
            raise HTTPBadRequest(reason="bad file field type")
        elif not (file.startswith('http://') or file.startswith('https://')):
            raise HTTPBadRequest(reason="'file' must be url")

        return (yield from self.resource.add(file))


class MPDSong(InitCoroMixin, MPDBase):
    def __init__(self, parent, name):
        super().__init__(parent, name)

        try:
            self.id = int(name)
        except ValueError:
            raise HTTPNotFound

    @asyncio.coroutine
    def __init_coro__(self):
        for item in (yield from self.mpd.playlist()):
            if item['id'] == self.id:
                break
        else:
            raise HTTPNotFound

    @asyncio.coroutine
    def get(self):
        playlist = yield from self.mpd.playlist()

        for song in playlist:
            if song['id'] == self.id:
                return song
        else:
            return None

    @asyncio.coroutine
    def play(self):
        return (yield from self.mpd.play(id=self.id))


class MPDSongView(RESTView):
    methods = {'get', 'put'}

    @asyncio.coroutine
    def get(self):
        return (yield from self.resource.get())

    @asyncio.coroutine
    def put(self):
        return (yield from self.resource.play())


def includeme(app):
    app.add_child(app._root_class, 'mpd', MPD)
    app.add_child(MPD, 'playlist', MPDPlaylist)

    app.bind_view(MPD, MPDView)
    app.bind_view(MPDPlaylist, MPDPlaylistView)
    app.bind_view(MPDSong, MPDSongView)
