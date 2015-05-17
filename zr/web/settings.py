import asyncio

from aiotraversal.resources import Resource
from aiotraversal.views import RESTView

from .mpd import MPD


class Settings(Resource):
    @asyncio.coroutine
    def get(self):
        return self.app.get('settings', {})


class SettingsView(RESTView):
    methods = {'get'}

    @asyncio.coroutine
    def get(self):
        data = (yield from self.resource.get())
        return {
            'playlists': data['playlists'],
        }


def includeme(app):
    app.add_child(MPD, 'settings', Settings)
    app.bind_view(Settings, SettingsView)
