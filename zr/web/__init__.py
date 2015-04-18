from .lib.resources import Root as BaseRoot
from .lib.static import StaticView


class Root(BaseRoot):
    path = 'zr/web/static/index.html'


def includeme(app):
    app.include('zr.web.lib.static')

    app.set_root_class(Root)
    app.setup_resource(Root, StaticView)
    app.add_static(Root, 'static', 'zr/web/static/')

    app.include('zr.web.mpd')
