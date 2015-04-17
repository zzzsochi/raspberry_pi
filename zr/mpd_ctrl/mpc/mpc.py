"""
MPD API documentation:
"""
import asyncio
import logging

from .playlist import Playlist
from .helpers import lock, lock_and_status, str_bool

log = logging.getLogger(__name__)

mpc_subprocesslocker = asyncio.Lock()


class MPDProtocol(asyncio.Protocol):
    def __init__(self, mpd):
        self.mpd = mpd

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        log.debug('connection to {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        log.debug('data received: {!r}'.format(data.decode()))
        self.mpd._received_data.put_nowait(data)

    def connection_lost(self, exc):
        log.debug('connection lost')
        if exc is not None:
            log.error('connection lost exc: {!r}'.format(exc))

        self.mpd._closed()
        asyncio.async(self.mpd._reconnect())


class MPD:
    """ Client for music player daemon
    """
    _status_casts = {
        'volume': int,
        'repeat': str_bool,
        'random': str_bool,
        'single': str_bool,
        'consume': str_bool,
        'playlist': int,
        'playlistlength': int,
        'song': int,
        'songid': int,
        'nextsong': int,
        'nextsongid': int,
        'duration': int,
        'xfade': int,
        'updating_db': int,
    }

    _transport = None
    _protocol = None
    _status = None

    def __init__(self):
        self._lock = asyncio.Lock()
        self._received_data = asyncio.Queue(maxsize=1)

    @classmethod
    @asyncio.coroutine
    def make_connection(cls, host='localhost', port=6600, loop=None):
        """ Classmethod for create the connection to mpd

        :param str host: hostname for connection (default `'localhost'`)
        :param int port: port for connection (default: `6600`)
        :param BaseEventLoop loop: event loop for `connect` method (default: None)
        :return: new MPD instance
        """
        mpd = cls()
        yield from mpd.connect(host, port, loop)
        return mpd

    def _closed(self):
        self._transport = None
        self._protocol = None
        self._status = None

    @asyncio.coroutine
    def _reconnect(self):
        return asyncio.async(self.connect(self._host, self._port, self._loop))

    @asyncio.coroutine
    def connect(self, host='localhost', port=6600, loop=None):
        """ Connect to mpd

        :param str host: hostname for connection (default `'localhost'`)
        :param int port: port for connection (default: `6600`)
        :param BaseEventLoop loop: event loop for `connect` method
            (default: `asyncio.get_event_loop()`)
        :return: pair `(transport, protocol)`
        """
        with (yield from self._lock):
            if loop is None:
                loop = asyncio.get_event_loop()

            self._host = host
            self._port = port
            self._loop = loop

            _pf = lambda: MPDProtocol(self)
            t, p = yield from loop.create_connection(_pf, host, port)
            self._transport = t
            self._protocol = p
            log.debug('connected to {}:{}'.format(host, port))

            yield from self._received_data.get()
            return (t, p)

    @asyncio.coroutine
    def _send_command(self, command, *args):
        args = [str(a) for a in args]
        prepared = '{}\n'.format(' '.join([command] + args))
        self._transport.write(prepared.encode('utf8'))
        log.debug('data sent: {!r}'.format(prepared))
        resp = yield from self._received_data.get()
        return resp

    @asyncio.coroutine
    def _get_status(self):
        raw = (yield from self._send_command('status')).decode('utf8')
        # lines = raw.split('\n')[:-2]
        # parsed = dict(l.split(': ', 1) for l in lines)
        # return {k: self._status_casts.get(k, str)(v) for k, v in parsed.items()}
        return {k: self._status_casts.get(k, str)(v) for k, v in
                (l.split(': ', 1) for l in raw.split('\n')[:-2])}

    @lock_and_status
    @asyncio.coroutine
    def get_status(self):
        return self._status

    @lock_and_status
    @asyncio.coroutine
    def play(self, track):
        yield from self._send_command('play', track)

    @lock_and_status
    @asyncio.coroutine
    def stop(self):
        yield from self._send_command('stop')

    @lock_and_status
    @asyncio.coroutine
    def toggle(self):
        if self._status['state'] == 'play':
            yield from self._send_command('pause', 1)
        elif self._status['state'] == 'pause':
            yield from self._send_command('pause', 0)
        elif self._status['state'] == 'stop':
            yield from self._send_command('play', 1)

    @lock_and_status
    def get_volume(self):
        return self._status['volume']

    @lock
    @asyncio.coroutine
    def set_volume(self, value):
        assert 0 <= value <= 100
        yield from self._send_command('setvol', value)

    @lock_and_status
    @asyncio.coroutine
    def incr_volume(self, value):
        assert -100 <= value <= 100
        volume = self._status['volume'] + value

        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100

        yield from self._send_command('setvol', volume)

    @lock_and_status
    @asyncio.coroutine
    def next(self, count=1):
        song = self._status['song'] + count
        if song >= self._status['playlistlength'] - 1:
            song = self._status['playlistlength'] - 1

        yield from self._send_command('play', song)

    @lock_and_status
    @asyncio.coroutine
    def prev(self, count=1):
        song = self._status['song'] - count
        if song < 0:
            song = 0

        yield from self._send_command('play', song)

    @lock_and_status
    @asyncio.coroutine
    def clear(self):
        yield from self._send_command('clear')

    @lock_and_status
    @asyncio.coroutine
    def add(self, uri):
        yield from self._send_command('add', uri)

    @lock_and_status
    @asyncio.coroutine
    def shuffle(self, start=None, end=None):
        assert start is None and end is None
        assert start is not None and end is not None

        if start is not None:
            yield from self._send_command('shuffle', '{}:{}'.format(start, end))

    @property
    def playlist(self):
        return Playlist(self)
