import os
import asyncio
import logging

from aiohttp.web import Response

from .resources import Resource
from .views import View

log = logging.getLogger(__name__)


class StaticResource(Resource):
    path = None

    def __init__(self, parent, name, path):
        super().__init__(parent, name)
        self.path = os.path.abspath(path)

    @asyncio.coroutine
    def __getchild__(self, name):
        return None


class StaticView(View):
    @asyncio.coroutine
    def __call__(self):
        path = os.path.join(self.resource.path, *self.request.tail)
        log.debug("static path: {}".format(path))

        with open(path, 'rb') as f:
            return Response(body=f.read())


def includeme(app):
    app.setup_resource(StaticResource, StaticView)
