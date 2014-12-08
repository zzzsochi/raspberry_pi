import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

from mpd import MPDClient


MPD_HOST = 'localhost'
MPD_PORT = 6600

logger = logging.getLogger(__name__)


@asyncio.coroutine
def sleep_to_time(time):
    now = datetime.now(tz=timezone.utc)

    if now.timetz() <= time:
        next_start = datetime.combine(now.date(), time)
    else:
        _date = (now + timedelta(days=1)).date()
        next_start = datetime.combine(_date, time)

    wait_seconds = (next_start - now).total_seconds()
    logger.info('wait {} seconds'.format(wait_seconds))
    yield from asyncio.sleep(wait_seconds)


@contextmanager
def get_client():
    client = MPDClient()
    client.connect(MPD_HOST, MPD_PORT)

    yield client

    client.close()
    client.disconnect()


def play(playlist, vol):
    with get_client() as client:
        logger.info('clear playlist')
        client.clear()

        for item in playlist:
            logger.info("add to playlist '{}'".format(item))
            client.add(item)

        logger.info("set volume {}%".format(vol))
        client.setvol(vol)

        logger.info("play random")
        client.play(random.randint(0, len(client.playlistinfo()) - 1))
