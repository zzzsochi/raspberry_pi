import asyncio
import struct
import subprocess
import logging

from zr.lib.nrf24 import NRF24

from zr.mpd_ctrl.mpc import MPD
from zr.mpd_ctrl.remote import MpdPipe
from zr.mpd_ctrl.scheduler import MPDScheduler


log = logging.getLogger(__name__)


class RadioController:
    _stop = True

    def __init__(self, mpd):
        self.mpd = mpd
        self.radio = radio = NRF24(csn=26, ce=24)

        with radio:
            radio.status = NRF24.STATUS.stand_by

            radio._registry['CONFIG']['EN_CRC'] = False
            radio._registry['CONFIG']['CRCO'] = 1
            radio._registry['RF_SETUP']['RF_DR'] = 1
            radio._registry['SETUP_AW']['AW'] = 0b11

            radio.channel = 13

            radio.pipes[0] = MpdPipe(mpd, self.radio, 0, queue_size=10)

    @asyncio.coroutine
    def start(self, interval):
        self._stop = False
        asyncio.sleep(0.5)  # for stable start radio

        yield from self._start_pipes()
        yield from self._main_circle(interval)
        yield from self._stop_pipes()

        self.radio.close()
        log.info('{}.coro stoped'.format(self.__class__.__name__))

    def stop(self):
        self._stop = True

    @asyncio.coroutine
    def _main_circle(self, interval):
        with self.radio:
            self.radio.status = NRF24.STATUS.rx  # blocking!!!

            while not self._stop:
                self.radio.read_rx_fifo()
                yield from asyncio.sleep(interval)

    @asyncio.coroutine
    def _start_pipes(self):
        self._pipes_tasks = []
        for pipe in self.radio.pipes.values():
            if hasattr(pipe, 'process_received_data_coro'):
                self._pipes_tasks.append(
                    asyncio.async(
                        pipe.process_received_data_coro()))

    @asyncio.coroutine
    def _stop_pipes(self):
        for pipe in self.radio.pipes.values():
            if hasattr(pipe, 'stop_coro'):
                pipe.stop_coro = True

        yield from asyncio.wait(self._pipes_tasks, timeout=2)

        for task in self._pipes_tasks:
            if not task.done():
                task.cancel()


@asyncio.coroutine
def radio_print_received_data(pipe):
    """ Coroutine for development
    """
    while True:
        raw = yield from pipe.receive_coro()

        try:
            data = raw.decode('ascii')
            print(data)
        except UnicodeDecodeError:
            print(raw)


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('zr.lib.nrf24').setLevel('INFO')
    logging.getLogger('zr.mpd_ctrl.mpc').setLevel('INFO')
    logging.getLogger('zr.mpd_ctrl.remote').setLevel('INFO')

    loop = asyncio.get_event_loop()
    tasks = []

    mpd = loop.run_until_complete(MPD.make_connection())

    mpd_scheduler = MPDScheduler(mpd=mpd)
    tasks.append(asyncio.async(mpd_scheduler.start()))

    radio_controller = RadioController(mpd=mpd)
    tasks.append(asyncio.async(radio_controller.start(interval=0.05)))


    try:
        loop.run_forever()
    except KeyboardInterrupt:
        mpd_scheduler.stop()
        radio_controller.stop()

        try:
            loop.run_until_complete(asyncio.wait(tasks, timeout=5))
        except Exception as exc:
            log.error('exception while coroutines stoped: {}'.format(type(exc)))
            log.error(exc)
            import traceback
            traceback.print_exc()

        loop.stop()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
