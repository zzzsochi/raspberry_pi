import os
import json
import asyncio
import signal
import functools
import logging

import aiompd

try:
    from zr.lib.nrf24 import NRF24
except ImportError:
    WITH_RADIO = False
else:
    WITH_RADIO = True

from zr.mpd_ctrl.remote import MpdPipe
from zr.mpd_ctrl.scheduler import MPDScheduler

from aiotraversal import Application as Web


log = logging.getLogger(__name__)


SETTINGS = os.path.expanduser('~/.zr.json')


def logging_setup():
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger('zr.lib.nrf24').setLevel('INFO')
    logging.getLogger('zr.mpd_ctrl.remote').setLevel('INFO')

    logging.getLogger('aiohttp').setLevel('INFO')
    logging.getLogger('aiompd').setLevel('INFO')


class RadioController:
    _stop = True

    def __init__(self, mpd):
        self.mpd = mpd
        self.radio = NRF24(csn=26, ce=24)

    @asyncio.coroutine
    def start(self, interval):
        self._stop = False

        radio = self.radio
        with radio:
            radio.status = NRF24.STATUS.stand_by

            radio._registry['CONFIG']['EN_CRC'] = False
            radio._registry['CONFIG']['CRCO'] = 1
            radio._registry['RF_SETUP']['RF_DR'] = 1
            radio._registry['SETUP_AW']['AW'] = 0b11

            radio.channel = 13

            radio.pipes[0] = MpdPipe(self.mpd, self.radio, 0, queue_size=10)

        yield from asyncio.sleep(0.1)  # for stable start radio

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
            if hasattr(pipe, 'task'):
                task = asyncio.async(pipe.task())
                self._pipes_tasks.append(task)

    @asyncio.coroutine
    def _stop_pipes(self):
        for pipe in self.radio.pipes.values():
            if hasattr(pipe, 'stop'):
                pipe.stop()

        yield from asyncio.wait(self._pipes_tasks, timeout=2)

        for task in self._pipes_tasks:
            if not task.done():
                task.cancel()


def exit_handler(loop, signame):
    log.info('got signal {}: exit'.format(signame))
    loop.stop()


def main():
    logging_setup()

    if os.path.isfile(SETTINGS):
        with open(SETTINGS) as f:
            settings = json.load(f)
    else:
        settings = {}

    loop = asyncio.get_event_loop()
    tasks = []

    mpd = loop.run_until_complete(aiompd.Client.make_connection())

    mpd_scheduler = MPDScheduler(mpd=mpd, settings=settings)
    tasks.append(asyncio.async(mpd_scheduler.start()))

    if WITH_RADIO:
        radio_controller = RadioController(mpd=mpd)
        tasks.append(asyncio.async(radio_controller.start(interval=0.05)))

    web = Web()
    web['mpd'] = mpd
    web['settings'].update(settings)
    web.include('zr.web')
    web.start(loop)

    for signame in ['SIGINT', 'SIGTERM']:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(exit_handler, loop, signame))

    try:
        loop.run_forever()

        mpd_scheduler.stop()

        if WITH_RADIO:
            radio_controller.stop()

        if tasks:
            try:
                loop.run_until_complete(asyncio.wait(
                    tasks + [asyncio.async(web.finish())],
                    timeout=5))
            except Exception as exc:
                loop.call_exception_handler({
                    'message': "Error in finish callback",
                    'exception': exc,
                })
    finally:
        loop.close()

if __name__ == '__main__':
    main()
