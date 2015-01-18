import asyncio
import struct
import logging

from zr.lib.nrf24.pipe import PipeAio

log = logging.getLogger(__name__)


class MpdPipe(PipeAio):
    stop_coro = True

    def __init__(self, mpd, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mpd = mpd

        self.address = 0xd1d2d3d2d1
        self.payload_length = 2
        self.auto_ack = False
        self.enabled = True

        self.stop_coro = False

    @asyncio.coroutine
    def process_received_data_coro(self):
        while not self.stop_coro:
            rc_future = asyncio.async(self.receive_coro())

            while not self.stop_coro:
                yield from asyncio.wait([rc_future], timeout=1)
                if rc_future.done():
                    raw = rc_future.result()
                    break
            else:
                rc_future.cancel()
                break

            log.debug('receiving data: {!r}'.format(raw))
            command, data = struct.unpack('cb', raw)
            log.debug('command {!r}, data: {!r}'.format(command, data))

            try:
                command = command.decode('ascii')
            except UnicodeDecodeError:
                log.error("bad command: {!r}".format(command))
                return

            if command == 'v':
                log.info('change volume: {}'.format(data))
                yield from self.mpd.incr_volume(data)

            elif command == 'p':
                log.info('pause')
                yield from self.mpd.toggle()

            elif command == 't':
                log.info('track: {}'.format(data))
                if data < 0:
                    yield from self.mpd.prev(count=abs(data))
                elif data > 0:
                    yield from self.mpd.next(count=data)
                else:
                    pass

            else:
                log.error('unknown command: {!r} ({!r})'.format(command, data))

        log.info('{}.process_received_data_coro stoped'.format(self.__class__.__name__))
