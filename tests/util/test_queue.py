from fidesops.util.queue import *


def test_queue() -> None:
    queue = Queue("A", "B", "B1", "C")
    assert queue.pop() == "A"
    assert queue.pop_first_match(lambda x: x.startswith("B")) == "B"
    assert queue.pop_first_match(lambda x: x.startswith("B")) == "B1"
    assert queue.pop_first_match(lambda x: x.startswith("B")) is None
    assert queue.is_empty() is False
    assert queue.data == ["C"]
    queue.push_if_new("C")
    assert queue.data == ["C"]
    queue.pop()
    queue.push_if_new("C")
    assert queue.data == ["C"]
