from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

T = TypeVar("T")


class MaxHeap(Generic[T]):
	"""Array-backed max heap ordered by a caller-provided comparable key."""

	def __init__(self, key: Callable[[T], tuple] | None = None) -> None:
		self._items: list[T] = []
		self._key = key or (lambda value: value)  # type: ignore[assignment,return-value]

	def __len__(self) -> int:
		return len(self._items)

	def is_empty(self) -> bool:
		return not self._items

	def _higher(self, left: T, right: T) -> bool:
		return self._key(left) > self._key(right)

	def push(self, item: T) -> None:
		self._items.append(item)
		index = len(self._items) - 1
		while index > 0:
			parent = (index - 1) // 2
			if not self._higher(self._items[index], self._items[parent]):
				break
			self._items[index], self._items[parent] = self._items[parent], self._items[index]
			index = parent

	def peek(self) -> T | None:
		return self._items[0] if self._items else None

	def pop_max(self) -> T | None:
		if not self._items:
			return None
		if len(self._items) == 1:
			return self._items.pop()
		maximum = self._items[0]
		self._items[0] = self._items.pop()
		self._sift_down(0)
		return maximum

	def _sift_down(self, index: int) -> None:
		size = len(self._items)
		while True:
			left = 2 * index + 1
			right = left + 1
			highest = index
			if left < size and self._higher(self._items[left], self._items[highest]):
				highest = left
			if right < size and self._higher(self._items[right], self._items[highest]):
				highest = right
			if highest == index:
				return
			self._items[index], self._items[highest] = self._items[highest], self._items[index]
			index = highest

	def rebuild(self, items: Iterable[T]) -> None:
		self._items = list(items)
		for index in range(len(self._items) // 2 - 1, -1, -1):
			self._sift_down(index)

	def copy(self) -> "MaxHeap[T]":
		duplicate = MaxHeap(self._key)
		duplicate._items = self._items.copy()
		return duplicate
