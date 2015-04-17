import asyncio

from .helpers import lock


class Playlist:
    def __init__(self, mpc):
        self.mpc = mpc
        self._transport = mpc._transport
        self._lock = mpc._lock

    @lock
    @asyncio.coroutine
    def list(self):
        raw = yield from self.mpc._send_command('playlistinfo')
        lines = raw.decode('utf8').split('\n')

        res = []

        for line in lines:
            if line == 'OK':
                break

            key, value = line.split(': ', 1)
            key = key.lower()

            if key == 'file':
                res.append({key: value})
            elif key in ['pos', 'id']:
                value = int(value)

            res[-1][key] = value

        return res

    @lock
    @asyncio.coroutine
    def clear(self, id):
        yield from self.mpc._send_command('clear')

    @lock
    @asyncio.coroutine
    def play(self, id):
        yield from self.mpc._send_command('playid', id)
