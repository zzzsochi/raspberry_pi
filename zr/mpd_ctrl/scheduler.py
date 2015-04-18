import asyncio
from datetime import datetime, time, timezone, timedelta
import logging

log = logging.getLogger(__name__)


NIGHT_TIME = time(23-3, 0, tzinfo=timezone.utc)
NIGHT_VOL_START = 35
NIGHT_MIDDLE_DURATION = timedelta(minutes=10)
NIGHT_VOL_MIDDLE = 50
NIGHT_END_DURATION = timedelta(hours=3)
NIGHT_VOL_END = 30
NIGHT_PLAYLIST = [
    'http://streaming.radionomy.com/SleepTime',
    'http://sc9106.xpx.pl:9106',
    'http://shurf.me:9480/nature96.aac',
]

MORNING_TIME = time(7-3, 0, tzinfo=timezone.utc)
MORNING_VOL_MIN = 10
MORNING_VOL_MAX = 20
MORNING_DURATION = timedelta(hours=1)
MORNING_PLAYLIST = [
    'http://mega5.fast-serv.com:8134',
    'http://74.86.186.4:10042',
    # 'http://174.36.51.212:10042',
    'http://s14.myradiostream.com:4668',
]


class MPDScheduler:
    _future_morning = None
    _future_nigth = None

    def __init__(self, mpd):
        self.mpd = mpd

    @asyncio.coroutine
    def start(self):
        self._future_morning = asyncio.async(self.morning())
        self._future_nigth = asyncio.async(self.nigth())

    def stop(self):
        self._future_morning.cancel()
        self._future_nigth.cancel()

    @asyncio.coroutine
    def nigth(self):
        while True:
            yield from self._sleep_to_time(NIGHT_TIME)
            yield from self._play(NIGHT_PLAYLIST, NIGHT_VOL_START)
            yield from self._gradual_increase_volume(NIGHT_MIDDLE_DURATION, NIGHT_VOL_MIDDLE)
            yield from self._gradual_increase_volume(NIGHT_END_DURATION, NIGHT_VOL_END)

    @asyncio.coroutine
    def morning(self):
        while True:
            yield from self._sleep_to_time(MORNING_TIME)
            yield from self._play(MORNING_PLAYLIST, MORNING_VOL_MIN)
            yield from self._gradual_increase_volume(MORNING_DURATION, MORNING_VOL_MAX)

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
