import asyncio
import logging

log = logging.getLogger(__name__)


@asyncio.coroutine
def traverse(root, path):
    """
    :param root: instance of Resource
    :param list path: ['events', 'event_id', 'sets', 'set_id']
    :return: `(resource, tail)`
    """
    if not path:
        return root, path

    path = path.copy()
    traverser = root[path.pop(0)]

    while path:
        traverser = traverser[path.pop(0)]

    return (yield from traverser.traverse())


class Traverser:
    _is_coroutine = True

    def __init__(self, resource, path):
        self.resource = resource
        self.path = path

    def __getitem__(self, item):
        return Traverser(self.resource, self.path + [item])

    @asyncio.coroutine
    def __iter__(self):
        """ This is work?
        """
        resource, tail = yield from self.traverse()

        if tail:
            raise KeyError(tail[0])
        else:
            return resource

    @asyncio.coroutine
    def traverse(self):
        """ Main traversal algorithm

        :return: tuple `(resource, tail)`
        """
        last, current = None, self.resource
        path = self.path.copy()

        while path:
            item = path[0]
            last, current = current, (yield from current.__getchild__(item))

            if current is None:
                return last, path

            del path[0]

        return current, path


def lineage(resource):
    while resource is not None:
        yield resource
        try:
            resource = resource.parent
        except AttributeError:
            resource = None
