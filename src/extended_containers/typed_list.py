import itertools
from contextlib import suppress
from typing import Any, Iterable, Optional, TypeVar, get_args, get_origin

_T = TypeVar("_T")


class TypedList(list[_T]):
    """A list of a specified Generic type

    With known type it is possible to remove or append a single list item
    without the usual gymnastics required by `<class list>`
    """

    def __init__(self, i: Optional[_T | Iterable[_T]] = None):
        super().__init__()
        if i:
            self.extend(i)

    def _check_param(self, p: _T | Iterable[_T]) -> Iterable[_T]:
        """Check the parameter `p` to see if it is a valid type"""
        GenericTypes = get_generic_types(self)
        ValidType = GenericTypes[0]
        _p = p if isinstance(p, Iterable) else (p,)

        for _i in _p:
            if not isinstance(_i, ValidType):
                raise TypeError(f"{_i=} type {type(_i)} not a {ValidType}")

        return _p

    def remove(self, r: _T | Iterable[_T]):
        """remove an item or items"""
        _r = self._check_param(r)

        with suppress(ValueError):
            for x in _r:
                super().remove(x)

    def extend(self, e: _T | Iterable[_T]) -> None:
        """extend with an item or items"""
        _e = self._check_param(e)

        super().extend(_e)


def get_generic_types(self: Any) -> tuple[type, ...]:
    """Return a Generic class instance's `TypeVar`s"""
    try:
        return self.__orig_class__.__args__
    except AttributeError:  # `self` is a sub-class of the typed Generic
        return tuple(
            itertools.chain.from_iterable(base.__args__ for base in self.__orig_bases__)
        )


def check_type(arg, expected_type):
    """check and argument `arg` for a specific type `expected_type`, e.g.
    ```py
        arg = [1, 2, 3]
        expected_type = List[int]

        print(check_type(arg, expected_type))
    ```
    """
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None:
        return isinstance(arg, expected_type)

    if not isinstance(arg, origin):
        return False

    if args:
        return all(isinstance(a, t) for a, t in zip(arg, args))

    return True
