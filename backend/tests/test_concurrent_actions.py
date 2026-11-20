import asyncio
import contextvars
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import agent
from agent import _actions_context, chat_with_agent, record_action
from main import app


def test_record_action_in_single_context():
    """Verify that record_action appends to the current context."""
    _actions_context.set([])
    assert _actions_context.get() == []

    record_action("Action 1")
    record_action("Action 2")

    actions = _actions_context.get()
    assert actions == ["Action 1", "Action 2"]


def test_actions_context_default_is_empty_list():
    """Verify default value for a new uninitialized context is an empty list."""
    ctx = contextvars.Context()
    val = ctx.run(_actions_context.get)
    assert val == []


def test_concurrent_threads_action_isolation():
    """Verify strict request-level isolation between concurrent threads."""
    results = {}

    def worker_thread(thread_id: int):
        # Initialize context for this thread
        _actions_context.set([])

        record_action(f"Thread-{thread_id}-Action-1")
        time.sleep(0.05)  # Simulate concurrent processing overlap
        record_action(f"Thread-{thread_id}-Action-2")
        time.sleep(0.05)

        results[thread_id] = list(_actions_context.get())

    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify that each thread recorded only its own actions with zero crosstalk
    for i in range(10):
        expected = [f"Thread-{i}-Action-1", f"Thread-{i}-Action-2"]
        assert results[i] == expected, f"Thread {i} actions leaked or corrupted: {results[i]}"


@pytest.mark.asyncio
async def test_async_tasks_action_isolation():
    """Verify strict isolation across asynchronous coroutine contexts."""
    results = {}

    async def async_worker(task_id: int):
        _actions_context.set([])
        record_action(f"Task-{task_id}-Step-1")
        await asyncio.sleep(0.05)
        record_action(f"Task-{task_id}-Step-2")
        await asyncio.sleep(0.05)
        results[task_id] = list(_actions_context.get())

    ctx1 = contextvars.copy_context()
    ctx2 = contextvars.copy_context()
    ctx3 = contextvars.copy_context()

    await asyncio.gather(
        asyncio.create_task(ctx1.run(async_worker, 1)),
        asyncio.create_task(ctx2.run(async_worker, 2)),
        asyncio.create_task(ctx3.run(async_worker, 3)),
    )

    for i in range(1, 4):
        expected = [f"Task-{i}-Step-1", f"Task-{i}-Step-2"]
        assert results[i] == expected, f"Task {i} actions leaked: {results[i]}"


def test_backward_compatible_actions_taken_attribute():
    """Verify that agent._actions_taken property seamlessly reads current context."""
    _actions_context.set([])
    record_action("Legacy Check 1")
    record_action("Legacy Check 2")

    # Access via module getattr
    assert agent._actions_taken == ["Legacy Check 1", "Legacy Check 2"]

    # Verify non-existent attributes still raise AttributeError
    with pytest.raises(AttributeError):
        _ = agent.non_existent_attribute_xyz


def test_chat_with_agent_initializes_clean_context():
    """Verify chat_with_agent clears stale actions from previous invocations in the context."""
    _actions_context.set(["Stale Action from previous request"])
    reply, actions = chat_with_agent("who has not marked today")
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert "Stale Action from previous request" not in actions


def test_concurrent_api_chat_requests():
    """Verify concurrent /api/chat endpoint calls maintain independent responses and states."""
    client = TestClient(app)

    queries = [
        "who has not marked today",
        "low attendance workers",
        "generate daily broadcast",
        "list workers",
    ]
    responses = {}

    def call_api(query: str):
        res = client.post("/api/chat", json={"message": query})
        responses[query] = res

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(call_api, queries))

    for query in queries:
        res = responses[query]
        assert res.status_code == 200
        body = res.json()
        assert "reply" in body
        assert "actions_taken" in body
        assert isinstance(body["actions_taken"], list)
