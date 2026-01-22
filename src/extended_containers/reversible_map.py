# standard library imports
from typing import Generic, NewType, Protocol, Self, TypeVar

# third party library imports

# typing
HashedKey = NewType("HashedKey", int)  # A *branded* hashed key for use by HashableModel
K = TypeVar("K") # forward key type
R = TypeVar("R", bound="Reversible")  # ReversibleModel type support
RK = TypeVar("RK")  # identity / reverse key type

class Reversible(Protocol[RK]):
    @property
    def identity(self) -> RK: ...


class ReversibleMap(Generic[K, R], dict[K, R]):
    _reversed: dict[HashedKey, K]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reversed = {HashedKey(hash(v.identity)): k for k, v in self.items()}

    def __setitem__(self, key: K, value: R) -> None:
        super().__setitem__(key, value)
        self._reversed[HashedKey(hash(value.identity))] = key

    def __delitem__(self, key: K) -> None:
        value = self[key]
        super().__delitem__(key)
        del self._reversed[HashedKey(hash(value.identity))]

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        for k, v in self.items():
            self._reversed[HashedKey(hash(v.identity))] = k

    def __ior__(self, other: dict[K, R]) -> Self:
        self.update(other)
        return self

    def rget(self, key: R | K) -> K:
        # Accept either the model instance (T) or the raw attribute HK used by T.__hash__
        hv = hash(key.identity) if hasattr(key, "identity") else hash(key)
        return self._reversed[HashedKey(hv)]
