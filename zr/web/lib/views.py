import json
import asyncio

from aiohttp.web import Response, HTTPMethodNotAllowed

from .abc import AbstractView


class View(AbstractView):
    def __init__(self, resource):
        self.resource = resource
        self.request = self.resource.request

    @asyncio.coroutine
    def __call__(self):
        raise NotImplementedError
        # return Response(body=self.request.path.encode('utf8'))


class MethodsView(View):
    methods = frozenset()  # {'get', 'post', 'put', 'patch', 'delete', 'option'}

    @asyncio.coroutine
    def __call__(self):
        method = self.request.method.lower()

        if method in self.methods:
            return (yield from getattr(self, method)())
        else:
            raise HTTPMethodNotAllowed(method, self.methods)

    @asyncio.coroutine
    def get(self):
        raise NotImplementedError

    @asyncio.coroutine
    def post(self):
        raise NotImplementedError

    @asyncio.coroutine
    def put(self):
        raise NotImplementedError

    @asyncio.coroutine
    def patch(self):
        raise NotImplementedError

    @asyncio.coroutine
    def delete(self):
        raise NotImplementedError

    @asyncio.coroutine
    def option(self):
        raise NotImplementedError


def jsonify(coro):
    @asyncio.coroutine
    def wrapper(self):
        data = yield from coro(self)
        return Response(body=json.dumps(data).encode('utf8'))

    return wrapper


class RESTView(MethodsView):
    @jsonify
    def __call__(self):
        return (yield from super().__call__())
