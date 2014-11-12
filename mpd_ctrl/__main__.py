#!/usr/bin/env python

import asyncio
import logging

from mpd_ctrl.morning import morning
from mpd_ctrl.night import night


def main():
    logging.basicConfig(level=logging.DEBUG)

    tasks = [
        asyncio.async(night()),
        asyncio.async(morning()),
    ]
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        loop.stop()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
