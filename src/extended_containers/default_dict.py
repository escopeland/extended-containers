from ast import TypeVar
from typing import Callable, Generator

_V = TypeVar("_V")


class DefaultDict(dict[str, _V]):
    """A dictionary with a default value"""

    def __init__(self, *args, default: _V | None = None, exec: bool = False, **kwargs):
        self.default: _V | Callable[[], _V] | None = default
        self.exec: bool = exec
        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        return self.default() if callable(self.default) and self.exec else self.default


class Dispatcher(DefaultDict[_V]):
    """A dispatch dictionary"""

    def __init__(self, default: _V | None = None):
        super().__init__(default=default, exec=False)

    def __call__(self, key: str, *args, **kwargs) -> _V:
        value = self[key]
        return value(*args, **kwargs) if callable(value) else value

    def __missing__(self, key):
        if self.default is None:
            raise KeyError("Dispatcher has no default")
        return super().__missing__(key)

    def register(self, keys, dispatch):
        """Register a dispatch key"""
        self |= dict.fromkeys(get_iter(keys), dispatch)


def get_iter(values):
    """Returns an iterable

    If values is a tuple, list or set, return an iterable for the list, set,
    or tuple members. Otherwise return values as one element tuple.

    All this is used for is making it possible to iterate over something
    that you don't know whether its a list or a single element.

    Note that if the elements in values are themselves iterables, they are
    not chained in any way. That is; a single iterable passed in values is
    returned as a one element tuple with values as that one element
    """
    return (
        iter(values)
        if isinstance(values, (tuple, list, set, filter, map, Generator))
        else iter((values,))
    )
