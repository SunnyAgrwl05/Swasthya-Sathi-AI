from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models
from agent import (
    chat_with_agent,
    _resolve_worker,
    record_action,
    get_actions,
    _actions_var,
    generate_daily_broadcast,
)

client = TestClient(app)


def test_chat_agent_fallback_tool_execution():
    # Test local intent fallback tool execution
    reply, actions = chat_with_agent("who has not marked today")
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert len(actions) > 0


def test_chat_endpoint():
    response = client.post("/api/chat", json={"message": "list workers"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "actions_taken" in data


def test_resolve_worker_name_collision_and_disambiguation():
    db = SessionLocal()
    try:
        # Create two workers with the exact same name but different sub-centers
        w1 = models.HealthWorker(
            worker_code="HW-POOJA-01",
            name="Pooja Sharma",
            role="ANM",
            phone="9876543210",
            center="Danapur Sub-Center",
        )
        w2 = models.HealthWorker(
            worker_code="HW-POOJA-02",
            name="Pooja Sharma",
            role="ASHA",
            phone="9876543211",
            center="Patna Central PHC",
        )
        db.add(w1)
        db.add(w2)
        db.commit()
        db.refresh(w1)
        db.refresh(w2)

        # 1. Disambiguation via composite string e.g. "Pooja Sharma (Danapur Sub-Center)"
        resolved_danapur = _resolve_worker(db, "Pooja Sharma (Danapur Sub-Center)")
        assert resolved_danapur is not None
        assert resolved_danapur.id == w1.id
        assert resolved_danapur.center == "Danapur Sub-Center"

        # 2. Disambiguation via query containing center name
        resolved_patna = _resolve_worker(db, "Pooja Sharma Patna Central")
        assert resolved_patna is not None
        assert resolved_patna.id == w2.id
        assert resolved_patna.center == "Patna Central PHC"

        # 3. Direct ID resolution
        resolved_by_id = _resolve_worker(db, f"#{w1.id}")
        assert resolved_by_id is not None
        assert resolved_by_id.id == w1.id

    finally:
        db.rollback()
        # Clean up test rows
        db.query(models.HealthWorker).filter(models.HealthWorker.name == "Pooja Sharma").delete()
        db.commit()
        db.close()


def test_actions_taken_contextvar_concurrency():
    """Verify concurrent requests isolate action logs without cross-thread contamination."""
    def worker_task(thread_id: int):
        actions = []
        token = _actions_var.set(actions)
        try:
            for i in range(5):
                record_action(f"Thread-{thread_id}-Action-{i}")
            return list(get_actions())
        finally:
            _actions_var.reset(token)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_task, i) for i in range(4)]
        results = [f.result() for f in futures]

    for i, res in enumerate(results):
        assert len(res) == 5
        for action in res:
            assert f"Thread-{i}-Action-" in action
            # Must NOT contain actions from other threads
            for other_id in range(4):
                if other_id != i:
                    assert f"Thread-{other_id}-Action-" not in action


def test_newly_registered_worker_not_flagged_as_delinquent():
    """Verify newly registered workers with 0 logs are not falsely flagged with 0.0% attendance."""
    db = SessionLocal()
    try:
        new_worker = models.HealthWorker(
            worker_code="HW-NEW-99",
            name="Rani Devi (New Recruit)",
            role="ASHA",
            phone="9123456789",
            center="Kalyanpur Health Center",
        )
        db.add(new_worker)
        db.commit()
        db.refresh(new_worker)

        broadcast = generate_daily_broadcast()
        # Rani Devi has 0 records; she must NOT appear under "Workers Requiring Follow-up (0.0%)"
        assert "Rani Devi (New Recruit) (0.0%)" not in broadcast
        assert "Rani Devi (New Recruit) (0%)" not in broadcast
    finally:
        db.query(models.HealthWorker).filter(models.HealthWorker.name == "Rani Devi (New Recruit)").delete()
        db.commit()
        db.close()
