import asyncio
import queue
from datetime import timedelta

from bytewax.inputs import batch, batch_async, batch_getter, batch_getter_ex
from pytest import raises


def test_batch():
    batcher = batch(range(5), 3)
    assert next(batcher) == [0, 1, 2]
    assert next(batcher) == [3, 4]
    with raises(StopIteration):
        next(batcher)
    with raises(StopIteration):
        next(batcher)


class CloseableQueue:
    def __init__(self):
        self.q = []
        self.closed = False

    def put(self, x):
        assert not self.closed
        self.q.append(x)

    def get(self):
        try:
            return self.q.pop(0)
        except IndexError:
            if not self.closed:
                raise queue.Empty() from None
            else:
                raise StopIteration() from None

    def close(self):
        self.closed = True


def test_batch_getter():
    q = CloseableQueue()

    def getter():
        try:
            return q.get()
        except queue.Empty:
            return None

    batcher = batch_getter(getter, 3)
    q.put(0)
    q.put(1)
    q.put(2)
    q.put(3)
    q.put(4)
    assert next(batcher) == [0, 1, 2]
    assert next(batcher) == [3, 4]
    assert next(batcher) == []
    q.put(5)
    q.close()
    assert next(batcher) == [5]
    with raises(StopIteration):
        next(batcher)
    with raises(StopIteration):
        next(batcher)


def test_batch_getter_ex():
    q = CloseableQueue()
    batcher = batch_getter_ex(q.get, 3)
    q.put(0)
    q.put(1)
    q.put(2)
    q.put(3)
    q.put(4)
    assert next(batcher) == [0, 1, 2]
    assert next(batcher) == [3, 4]
    assert next(batcher) == []
    q.put(5)
    q.close()
    assert next(batcher) == [5]
    with raises(StopIteration):
        next(batcher)
    with raises(StopIteration):
        next(batcher)


async def _gen():
    for i in range(5):
        await asyncio.sleep(0)
        yield i


def test_batch_async():
    batcher = batch_async(_gen(), timeout=timedelta(seconds=1), batch_size=2)
    assert next(batcher) == [0, 1]
    assert next(batcher) == [2, 3]
    assert next(batcher) == [4]
    with raises(StopIteration):
        next(batcher)
    with raises(StopIteration):
        next(batcher)
