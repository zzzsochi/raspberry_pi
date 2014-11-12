import asyncio
import logging
from datetime import time, timezone

from .lib import sleep_to_time, get_client, play


MPD_NIGHT_TIME = time(23-3, 0, tzinfo=timezone.utc)
MPD_NIGHT_VOL = 60
MPD_NIGHT_PLAYLIST = [
    'http://streaming.radionomy.com/SleepTime',
    'http://shurf.me:9480/nature96.aac',
]

logger = logging.getLogger(__name__)


@asyncio.coroutine
def night():
    while True:
        yield from sleep_to_time(MPD_NIGHT_TIME)
        play(MPD_NIGHT_PLAYLIST, 60)
