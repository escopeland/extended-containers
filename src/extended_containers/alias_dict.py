from typing import Mapping


class AliasDict[V](dict[str, V]):
    """
    A dict that stores only canonical keys internally, but allows
    reads/writes/deletes using alias keys as well.
    Iteration and repr always show canonical keys.
    """

    def __init__(
        self,
        data: Mapping[str, V] | None = None,
        aliases: Mapping[str, str] | None = None,
    ):
        super().__init__()
        # normalize to a dict for O(1) lookups
        self._aliases: dict[str, str] = dict(aliases) if aliases else {}
        if data:
            self.update(data)

    def _canonical(self, key: str) -> str:
        return self._aliases.get(key, key)

    # --- core ---

    def __getitem__(self, key: str) -> V:
        return super().__getitem__(self._canonical(key))

    def __setitem__(self, key: str, value: V) -> None:
        super().__setitem__(self._canonical(key), value)

    def __delitem__(self, key: str) -> None:
        super().__delitem__(self._canonical(key))

    def __contains__(self, key: object) -> bool:
        return super().__contains__(self._canonical(key))  # type: ignore

    def get(self, key: str, default: V | None = None) -> V | None:
        return super().get(self._canonical(key), default)

    def pop(self, key: str, default=...):
        canon = self._canonical(key)
        if default is ...:
            return super().pop(canon)
        return super().pop(canon, default)

    def update(self, other: Mapping[str, V] | None = None, **kwargs: V) -> None:
        if other:
            for k, v in other.items():
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    # --- introspection ---

    def aliases_for(self, canonical: str) -> list[str]:
        """Return all aliases that map to the given canonical key."""
        return [alias for alias, target in self._aliases.items() if target == canonical]

    def canonical_for(self, alias: str) -> str | None:
        """Return the canonical key for a given alias, or None if not found."""
        return self._aliases.get(alias)

    # --- representation ---

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self)}, aliases={self._aliases})"


