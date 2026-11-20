import asyncio
from concurrent.futures import ThreadPoolExecutor
import pytest

from agent import (
    _actions_context,
    _actions_taken,
    clear_recorded_actions,
    get_recorded_actions,
    record_action,
)


def test_actions_context_basic():
    clear_recorded_actions()
    assert get_recorded_actions() == []
    record_action("Action 1")
    record_action("Action 2")
    assert get_recorded_actions() == ["Action 1", "Action 2"]
    clear_recorded_actions()
    assert get_recorded_actions() == []


def test_actions_proxy_backward_compatibility():
    clear_recorded_actions()
    _actions_taken.append("Proxy Action")
    assert len(_actions_taken) == 1
    assert list(_actions_taken) == ["Proxy Action"]
    assert bool(_actions_taken) is True
    _actions_taken.clear()
    assert len(_actions_taken) == 0
    assert bool(_actions_taken) is False


@pytest.mark.asyncio
async def test_actions_context_async_concurrency():
    async def worker_task(task_id: int):
        # Reset context for this specific coroutine
        _actions_context.set([])
        record_action(f"Task-{task_id}-Start")
        await asyncio.sleep(0.01 * (task_id % 3 + 1))
        record_action(f"Task-{task_id}-End")

        actions = get_recorded_actions()
        assert len(actions) == 2, f"Task {task_id} had unexpected actions: {actions}"
        assert actions[0] == f"Task-{task_id}-Start"
        assert actions[1] == f"Task-{task_id}-End"
        return actions

    # Run 20 concurrent coroutines
    tasks = [worker_task(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 20


def test_actions_context_thread_concurrency():
    def thread_worker(worker_id: int):
        _actions_context.set([])
        record_action(f"Worker-{worker_id}-1")
        import time
        time.sleep(0.02)
        record_action(f"Worker-{worker_id}-2")

        actions = get_recorded_actions()
        assert len(actions) == 2, f"Worker {worker_id} contaminated with: {actions}"
        assert actions[0] == f"Worker-{worker_id}-1"
        assert actions[1] == f"Worker-{worker_id}-2"
        return actions

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(thread_worker, i) for i in range(16)]
        for f in futures:
            assert len(f.result()) == 2
