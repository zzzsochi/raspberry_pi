import asyncio
import random
import logging
from datetime import time, timezone, timedelta

from .lib import sleep_to_time, get_client, play

MPD_MORNING_TIME = time(7-3, 0, tzinfo=timezone.utc)
MPD_MORNING_DURATION = timedelta(seconds=60*60)
MPD_MORNING_VOL_MIN = 40
MPD_MORNING_VOL_MAX = 70
MPD_MORNING_PLAYLIST = [
    'http://174.36.51.212:10042',
    'http://s14.myradiostream.com:4668',
    'http://pub4.radiotunes.com:80/radiotunes_poppunk',
]


logger = logging.getLogger(__name__)


@asyncio.coroutine
def _morning_increase_volume():
    count = MPD_MORNING_VOL_MAX - MPD_MORNING_VOL_MIN
    delay = MPD_MORNING_DURATION.total_seconds() / count

    for vol in range(MPD_MORNING_VOL_MIN + 1, MPD_MORNING_VOL_MAX + 1):
        logger.debug("wait {} seconds for increase volume".format(delay))
        yield from asyncio.sleep(delay)
        with get_client() as client:
            logger.info("set volume {}%".format(vol))
            client.setvol(vol)


@asyncio.coroutine
def morning():
    while True:
        yield from sleep_to_time(MPD_MORNING_TIME)
        play(MPD_MORNING_PLAYLIST, MPD_MORNING_VOL_MIN)
        yield from _morning_increase_volume()
