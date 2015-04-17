import asyncio
import logging

from .traversal import Traverser

log = logging.getLogger(__name__)


class Resource:
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.request = parent.request
        self.app = self.request.app
        self.setup = self.app['resources'].get(self.__class__)

    def __getitem__(self, name):
        return Traverser(self, [name])

    @asyncio.coroutine
    def __getchild__(self, name):
        raise NotImplementedError


class Root(Resource):
    def __init__(self, request):
        self.parent = None
        self.name = None
        self.request = request
        self.app = request.app

    @asyncio.coroutine
    def __getchild__(self, name):
        return self
