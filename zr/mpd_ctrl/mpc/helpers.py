import types
import asyncio

import logging

log = logging.getLogger(__name__)


def lock(func):
    # lock method
    def wrapper(self, *args, **kwargs):
        if self._transport is None:
            log.error("connection closed")
            raise RuntimeError("connection closed")

        with (yield from self._lock):
            return (yield from (func(self, *args, **kwargs)))

    return wrapper


def lock_and_status(func):
    # lock, get last status from mpd and run method
    @asyncio.coroutine
    def wrapper(self, *args, **kwargs):
        if self._transport is None:
            log.error("connection closed")
            raise RuntimeError("connection closed")

        with (yield from self._lock):
            self._status = yield from self._get_status()

            res = func(self, *args, **kwargs)
            if isinstance(res, types.GeneratorType):
                return (yield from res)
            else:
                return res

    return wrapper


str_bool = lambda v: v != '0'
