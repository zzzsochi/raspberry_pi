#!/usr/bin/env /home/pi/.pyenv/versions/3.4.2/bin/python

import time
import random
from contextlib import contextmanager

from mpd import MPDClient


SOURCES = [
    'http://108.61.20.171:10042',
    'http://pub4.radiotunes.com:80/radiotunes_poppunk',
    'http://s14.myradiostream.com:4668/',
]


@contextmanager
def get_client():
    client = MPDClient()
    client.connect("localhost", 6600)

    yield client

    client.close()
    client.disconnect()


def playlist_check():
    with get_client() as client:
        return bool(len(client.playlistinfo()))


def playlist_fill():
    with get_client() as client:
        for source in SOURCES:
            client.add(source)


def play(start_vol=0):
    with get_client() as client:
        client.setvol(start_vol)
        client.play(random.randint(0, len(client.playlistinfo()) - 1))


def volume_up(min_vol, max_vol, interval):
    with get_client() as client:
        for vol in range(min_vol, max_vol+1):
            time.sleep(interval)
            client.setvol(vol)


if __name__ == '__main__':
    if not playlist_check():
        playlist_fill()

    play()
    volume_up(40, 70, 120)
