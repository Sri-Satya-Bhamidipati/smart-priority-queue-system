from app.core.heap import MaxHeap


def test_max_heap_extracts_highest_first():
	heap = MaxHeap(key=lambda value: value)
	for value in [3, 10, 1, 7, 5]:
		heap.push(value)
	assert [heap.pop_max() for _ in range(5)] == [10, 7, 5, 3, 1]
	assert heap.pop_max() is None


def test_heap_rebuild_and_peek():
	heap = MaxHeap(key=lambda value: value)
	heap.rebuild([4, 12, 2, 8])
	assert heap.peek() == 12
	assert len(heap) == 4
