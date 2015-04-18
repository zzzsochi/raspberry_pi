import os
import asyncio
import logging

from aiohttp.web import Response

from .resources import Resource
from .views import View

log = logging.getLogger(__name__)


class StaticResource(Resource):
    path = None

    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.path = os.path.abspath(self.path)

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


def add_static(app, parent, name, path, resource_class=StaticResource):
    """ Add resource for serve static
    """
    SRes = type(resource_class.__name__, (resource_class,), {'path': path})
    app.add_child(parent, name, SRes)


def includeme(app):
    app.add_method('add_static', add_static)
    app.bind_view(StaticResource, StaticView)
