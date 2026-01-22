# standard imports
from typing import Protocol, TypeVar, cast

################################################################################
# `<class NestedDict>` and supporting types, methods
################################################################################
T = TypeVar("T", bound="HasNDParent")


class HasNDParent(Protocol):
    parent: NestedDict | None


class NestedDict(dict[str, "NestedDict[T]" | T]):
    """A nested dictionary hierarchy accessed by a list of keys.

    A `node` refers to any `<class NestedDict>` instance in a hierachy of nested
    dictionaries, `root` refers to the top-level node, `branch` refers to any
    intermediate-level node, and `leaf` refers to the lowest-level nodes having
    type `T` values. `root` and `branch` nodes have `Generic` type `NestedDict`
    values.

    **Attributes**
    - `parent: NestedDict` the parent `node` in the nested dictionary hierarchy,
       used to enable traversal up the hiearchy towards the `root`.
    - `_key: str` the name of the key used by the parent `NestedDict` to access
      `self`.
    - `__chainmap__: dict[str, T]` a dictionary used to access leaf node values
       directly without the need for a recursive tree traversal.

    **Notes**
    - `set()` makes type checks during hierarchy construction to:
      1. ensure that the hierarchy construction is correct; and,
      2. allow `get()` to skip type checks.
      Logically, this assumes that hierarchy construction occurs only once but
      node indexing can occur many times.
    """

    def __init__(
        self, *args, parent: NestedDict[T] | None = None, key: str | None = None, **kwargs
    ):
        self.parent = parent
        self._key = key
        self.__chainmap__: dict[str, T] = {}
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"{type(self).__name__}(key={self.key}, {super().__repr__()})"

    def __contains__(self, key):
        """Return `True` if `key` returns a `leaf` node in the hierarchy.

        **Parameters**
        - `key: str` a string with `.`s separating the individual keys required
           to traverse the hierarchy and target the desired `leaf` node.
        """
        self_key, _, node_key = cast(str, key).partition(".")
        if super(NestedDict, self).__contains__(self_key):
            if not node_key:  # stop recursion when branch is a leaf node
                return True
            # continue branch node recursion
            branch = self[self_key]
            return isinstance(branch, NestedDict) and branch.__contains__(node_key)
        return False

    @property
    def key(self) -> str:
        """Return the `key` required to find `self` from `root` using `get()`."""
        parent = self.parent
        if parent and parent.key:
            return f"{parent.key}.{self._key}"
        return self._key or ""

    @property
    def chainmap(self):
        return self.__chainmap__

    def set(self, key: str, value: T) -> None:
        """Insert a new leaf value into the nested dictionary hierarchy.

        **Parameters**
        - `key: str` a dot-separated composite key of the form
           `<root key>.<branch key>....<leaf key>`
           targeting either a `branch` node or a `leaf` node value.
        - `value: T` the value to insert into the `leaf` node.
        """
        self.__chainmap__[key] = value
        self_key, _, node_key = key.partition(".")
        if node_key:  # continue branch node recursion
            next_branch = self.get(self_key)
            if next_branch is None or not isinstance(next_branch, NestedDict):
                next_branch = NestedDict(parent=self, key=self_key)
            self[self_key] = next_branch
            next_branch.set(node_key, value)
        else:  # stop recursion when branch is a leaf node
            value.parent = self
            self[self_key] = value

    def get(self, key: str, default=None) -> NestedDict[T] | T:
        """Recursively retrieve a `leaf` value from the hierarchy.

        **Parameters**
        - `key: str` a dot-separated composite key of the form:
           `<root key>.<branch key>....<leaf key>`
           targeting either a `branch` node or a `leaf` node value.
        - `default: T` the value to return if `key` is not in the hierarchy`.
        """
        self_key, _, node_key = key.partition(".")
        branch = super(NestedDict, self).get(self_key, default)
        if not node_key:  # stop recursion when `branch` is a `leaf` node
            return branch
        if isinstance(branch, NestedDict):  # continue `branch` node recursion
            return branch.get(node_key, default)
        return default

    def get_leaf(self, key: str) -> T:
        """Directly retrieve a `leaf` value from the nested dictionary hierarchy.

        Speeds up access if you know `key` addresses a `leaf` node.

        **Parameters**
        - `key: str` a dot-separated composite key of the form:
           `<root key>.<branch key>....<leaf key>`
           targeting a `leaf` node value.

        **Returns**
        - `T` a  `leaf` node value.
        """
        return self.__chainmap__[key]

    def delete_key(self, key: str):
        """Delete a node from the `NestedDict` hierarchy.

        **Parameters**
        - `key: str` a dot-separated composite key of the form:
           `<root key>.<branch key>....<leaf key>`
           targeting either a `branch` node or a `leaf` node.
        """
        # delete `leaf` keys associated with `key` in `self.__chainmap__`: you
        # can't modify a dictionary in place so construct keys to delete first.
        leaf_keys_to_delete = {k for k in self.__chainmap__ if k.startswith(key)}
        for leaf_key in leaf_keys_to_delete:
            del self.__chainmap__[leaf_key]
        # now traverse the hierarchy and delete `nodes` addressed by `key`
        self_key, _, node_key = key.partition(".")
        if not node_key:  # stop recursion when `branch` is a `leaf` node
            del self[self_key]
        else:  # continue branch node recursion
            sub_node = cast(NestedDict, self[self_key])
            sub_node.delete_key(node_key)

    def clear(self):
        self.__chainmap__.clear()
        super().clear()
