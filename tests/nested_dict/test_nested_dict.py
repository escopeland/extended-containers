from __future__ import annotations

# standard imports
from typing import Protocol, TypeVar, cast

################################################################################
# `<class NestedDict>` and supporting types, methods
################################################################################
T = TypeVar("T", bound="HasNDParent")


class HasNDParent(Protocol):
    parent: NestedDict | None


class Pint(int):
    parent: NestedDict | None


class NestedDict(dict[str, "NestedDict[T]" | T]):
    """A nested dictionary hierarchy accessed by a list of keys.

    A `node` refers to any `<class NestedDict>` instance in a hierachy of nested
    dictionaries, `root` refers to the top-level node, `branch` refers to any
    intermediate-level nodes, and `leaf` refers to the lowest-level nodes having
    type `V` values. `root` and `branch` nodes have `Generic` type `T` values.

    **Attributes**
    - `parent: NestedDict` the parent `node` in the nested dictionary hierarchy,
       used to enable traversal up the hiearchy towards the `root`.
    - `_key: str` the name of the key used by the parent `NestedDict` to access
      `self`.
    - `_by_key: dict[str, T]` a dictionary used to access leaf node value
       directly without the need for a recursive tree traversal.

    **Notes**
    - `set()` makes type checks during hierarchy construction to:
      1. ensure that the hierarchy construction is correct; and,
      2. allow `get()` to skip type checks.
      Logically, this assumes that hierarchy construction occurs only once but
      that node indexing can occur many times.
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

        return key in self.__chainmap__

    @property
    def key(self) -> str:
        """Return the `key` required to find `self` from `root`."""

        parent = self.parent
        if parent and parent.key:
            return f"{parent.key}.{self._key}"
        return self._key or ""

    def set(self, key: str, value: T) -> None:
        """Insert a new leaf value into the nested dictionary hierarchy.

        **Parameters**
        - `key: str` a string with `.`s separating the individual keys required
           to traverse the hierarchy and target the desired `leaf` node.
        - `value: T` the value to insert into the `leaf` node.
        """

        self.__chainmap__[key] = value
        branch_key, _, node_key = key.partition(".")
        if node_key:  # continue branch node recursion
            next_branch = self.get(branch_key)
            if next_branch is None or not isinstance(next_branch, NestedDict):
                next_branch = NestedDict(parent=self, key=branch_key)
            self[branch_key] = next_branch
            next_branch.set(node_key, value)
        else:  # stop recursion when branch is a leaf node
            value.parent = self
            self[branch_key] = value

    def get(self, key: str, default=None) -> NestedDict[T] | T:
        """Recursively retrieve a `leaf` value from the hierarchy.

        **Parameters**
        - `key: str` a string with `.`s separating the individual keys required
           to traverse the hierarchy and target the desired `leaf` node.
        - `default: T` the value to return `key` is not in the hierarchy`.
        """
        branch_key, _, node_key = key.partition(".")
        branch = super(NestedDict, self).get(branch_key, default)
        if not node_key:
            return branch
        if isinstance(branch, NestedDict):
            return branch.get(node_key, default)
        return default

    def get_leaf(self, key: str) -> T:
        """Directly retrieve a leaf value from the nested dictionary hierarchy.

        Speeds up access if you konw the key is a `leaf` node key.

        **Parameters**
        - `key: str` a string with `.`s separating the individual keys required
           to traverse the hierarchy and target the desired `leaf` node.

        **Returns**
        - `T` a  `leaf` node value.
        """

        # TODO: See if this is ever called and, if not, delete it. It provides
        # direct access to the leaves via the dictionary.
        return self.__chainmap__[key]

    def delete_key(self, key: str):
        # delete `leaf` keys associated with `key` in `self.__chainmap__`: you
        # can't modify a dictionary in place so construct keys to delete first.
        leaf_keys_to_delete = {k for k in self.__chainmap__ if k.startswith(key)}
        for leaf_key in leaf_keys_to_delete:
            del self.__chainmap__[leaf_key]
        # now traverse the hierarchy and delete `nodes` addressed by `key`
        self_key, _, node_key = key.partition(".")
        if not node_key:  # key points to a `leaf` node of type `T`
            del self[self_key]
        else:  # key points to a `branch` node of type `NestedDict`
            sub_node = cast(NestedDict, self[self_key])
            sub_node.delete_key(node_key)
        pass


# Example usage
# nested: NestedDict[int] = NestedDict({"a": NestedDict({"b": NestedDict({"c": 42})}), "d": 99})
nested = NestedDict[Pint]()
nested.set("a.b.c", Pint(99))
nested.set("d", Pint(42))
print("a" in nested)  # Output: False
print("a.b" in nested)  # Output: False
print("a.b.c" in nested)  # Output: True
print("a.d.c.d" in nested)  # Output: False
print("a.d" in nested)  # Output: False
print("d" in nested)  # Output: True
print("z" in nested)  # Output: False

print(nested.get("a"))
print(nested.get("a.b"))
print(nested.get("a.b.c"))
print(nested.get("d"))
print(nested.get("z"))
print(nested.get("z", "NOT FOUND"))
print(nested.get("a.c", "NOT FOUND"))
print(nested.get("a.b.d", "NOT FOUND"))
print(nested.get("d.a.b", "NOT FOUND"))
print(nested.get("d.e.bf", "NOT FOUND"))

nested.delete_key("a.b.c")
nested.delete_key("a")
pass
