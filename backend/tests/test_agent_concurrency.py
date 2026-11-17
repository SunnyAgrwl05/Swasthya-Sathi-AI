"""Unit tests for agent actions_taken thread safety and concurrency isolation (fixes #59)."""

import concurrent.futures
import time

from agent import _actions_taken, _actions_taken_var


def simulate_request(req_id: int, num_actions: int = 5) -> list[str]:
    """Simulates a concurrent chat request appending actions to the thread-local state."""
    req_actions: list[str] = []
    token = _actions_taken_var.set(req_actions)
    try:
        for i in range(num_actions):
            action = f"req_{req_id}_action_{i}"
            _actions_taken.append(action)
            time.sleep(0.005)  # Yield to provoke race conditions if not isolated
        return list(_actions_taken)
    finally:
        _actions_taken_var.reset(token)


def test_concurrent_actions_isolation():
    """Verify that multiple concurrent threads do not bleed or overwrite _actions_taken."""
    num_threads = 10
    actions_per_thread = 8

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(simulate_request, thread_idx, actions_per_thread)
            for thread_idx in range(num_threads)
        ]
        results = [f.result() for f in futures]

    for thread_idx, res in enumerate(results):
        assert len(res) == actions_per_thread
        expected = [f"req_{thread_idx}_action_{i}" for i in range(actions_per_thread)]
        assert res == expected, f"Thread {thread_idx} actions were contaminated: {res}"


def test_actions_list_proxy_behavior():
    """Verify _ThreadSafeActionsList proxy behaves like a list."""
    # Test fallback behavior when no contextvar is explicitly set
    _actions_taken.clear()
    assert len(_actions_taken) == 0
    _actions_taken.append("test_item_1")
    _actions_taken.extend(["test_item_2", "test_item_3"])
    assert len(_actions_taken) == 3
    assert list(_actions_taken) == ["test_item_1", "test_item_2", "test_item_3"]
    assert bool(_actions_taken) is True
