import asyncio
from datetime import datetime, time, timezone, timedelta
import logging

log = logging.getLogger(__name__)


class MPDScheduler:
    def __init__(self, mpd, settings):
        self.mpd = mpd
        self.settings = settings

    @asyncio.coroutine
    def start(self):
        for name in self.settings['scheduler']:
            self._futures = [asyncio.async(self._start_task(name))]

    def stop(self):
        for f in self._futures:
            f.cancel()

    @asyncio.coroutine
    def _start_task(self, name):
        settings = self._get_settings(name)

        while True:
            yield from self._sleep_to_time(settings['start'])

            if settings['volume']:
                vol, dur = settings['volume'][0]

            playlist = self.settings['playlists'].get(settings['playlist'], [])
            yield from self._play(playlist, vol)

            for vol, dur in settings['volume']:
                if dur is None:
                    yield from self.mpd.set_volume(vol)
                else:
                    yield from self._gradual_increase_volume(dur, vol)

    def _get_settings(self, name):
        settings = self.settings['scheduler'][name]

        if isinstance(settings['start'], str):
            settings['start'] = time(
                *[int(i) for i in settings['start'].split(':')],
                tzinfo=timezone.utc)

        for n, item in enumerate(settings.setdefault('volume', []).copy()):
            if isinstance(item, int):
                settings['volume'][n] = [item, None]
            elif isinstance(item[1], int):
                settings['volume'][n][1] = timedelta(seconds=item[1])

        return settings

    @asyncio.coroutine
    def _sleep_to_time(self, time):
        now = datetime.now(tz=timezone.utc)

        if now.timetz() <= time:
            next_start = datetime.combine(now.date(), time)
        else:
            _date = (now + timedelta(days=1)).date()
            next_start = datetime.combine(_date, time)

        wait_seconds = (next_start - now).total_seconds()
        log.info('wait {} seconds for {:%Y-%m-%d %H:%M:%S}'
                 ''.format(wait_seconds, next_start))

        yield from asyncio.sleep(wait_seconds)

    @asyncio.coroutine
    def _play(self, playlist, vol):
        yield from self.mpd.clear()

        for item in playlist:
            yield from self.mpd.add(item)

        yield from self.mpd.set_volume(vol)
        yield from self.mpd.play(0)

    @asyncio.coroutine
    def _gradual_increase_volume(self, duration, vol):
        current_vol = yield from self.mpd.get_volume()
        count = vol - current_vol
        delay = duration.total_seconds() / abs(count)

        for _ in range(abs(count)):
            log.debug("wait {} seconds for increase volume".format(delay))
            yield from asyncio.sleep(delay)
            yield from self.mpd.incr_volume(-1 if count < 0 else +1)
