import types
import logging
import warnings

from aiohttp.web import Application as BaseApplication
from zope.dottedname.resolve import resolve

from .router import Router
from .resources import Root

log = logging.getLogger(__name__)


class Application(BaseApplication):
    """ Main application object
    """
    root_class = Root

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('router', Router(self))
        super().__init__(*args, **kwargs)

        self['resources'] = {}

    def start(self, loop):
        """ Start applisation and add to event loop
        """
        f = loop.create_server(self.make_handler(), '0.0.0.0', 8080)
        srv = loop.run_until_complete(f)
        log.info("start server: {!r}".format(srv))

    def include(self, name_or_func):
        """ Include external configuration
        """
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

    def add_method(self, name, func):
        """ Add method to application

        Usage from configuration process.
        """
        if hasattr(self, name):
            warnings.warn("method {} is already exist, replacing it"
                          "".format(name))

        meth = types.MethodType(func, self)
        setattr(self, name, meth)

    def set_root_class(self, root_class):
        """ Set root resource class

        Analogue of the "set_root_factory" method from pyramid framework.
        """
        self.root_class = root_class

    def get_root(self, request):
        """ Create new root resource instance
        """
        return self.root_class(request)

    def bind_view(self, resource, view):
        """ Bind view for resource
        """
        setup = self['resources'].setdefault(resource, {})
        setup['view'] = view
