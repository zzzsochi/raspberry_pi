import types
import logging

from aiohttp.web import Application as BaseApplication
from zope.dottedname.resolve import resolve

from .router import Router
from .resources import Root

log = logging.getLogger(__name__)


class Application(BaseApplication):
    root_factory = Root

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('router', Router(self))
        super().__init__(*args, **kwargs)

        self['resources'] = {}

    def start(self, loop):
        f = loop.create_server(self.make_handler(), '0.0.0.0', 8080)
        srv = loop.run_until_complete(f)
        log.info("start server: {!r}".format(srv))

    def include(self, name_or_func):
        if callable(name_or_func):
            name_or_func(self)
        else:
            func = resolve(name_or_func)

            if isinstance(func, types.ModuleType):
                if not hasattr(func, 'includeme'):
                    raise ImportError("{}.includeme".format(func.__name__))

                func = getattr(func, 'includeme')

            if not callable(func):
                raise ValueError("{}.includeme is not callable"
                                 "".format(func.__name__))

            func(self)

    def set_root_factory(self, root_factory):
        self.root_factory = root_factory

    def get_root(self, request):
        return self.root_factory(request)

    def setup_resource(self, resource, view=None, parent=None, name=None):
        assert ((parent is None and name is None)
                or (parent is not None and name is not None))

        setup = self['resources'].setdefault(resource, ResourceSetup())

        if view is not None:
            setup.view = view

        if parent is not None:
            parent_setup = self['resources'].setdefault(parent, ResourceSetup())
            parent_setup.children[name] = resource


class ResourceSetup:
    def __init__(self):
        self.view = None
        self.children = {}