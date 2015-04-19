from .lib.resources import Root as BaseRoot
from .lib.static import StaticView


class Root(BaseRoot):
    path = 'zr/web/static/index.html'


def includeme(app):
    app.include('.lib.resources')
    app.include('.lib.static')

    app.set_root_class(Root)
    app.bind_view(Root, StaticView)
    app.add_static(Root, 'static', 'zr/web/static/')

    app.include('.mpd')
