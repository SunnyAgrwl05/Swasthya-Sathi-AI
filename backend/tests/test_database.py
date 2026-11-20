import models


def test_models_relationships_and_constraints(db_session):
    worker = models.HealthWorker(
        worker_code="DB-TEST-1",
        name="Test Worker",
        role="ASHA",
        center="Patna Center",
        phone="9988776655"
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    assert worker.id is not None

    chat_log = models.ChatLog(role="user", message="Hello Swasthya Sathi")
    agent_log = models.AgentLog(
        query="Attendance query",
        response="Here is summary",
        tools_used="get_attendance_summary",
        status="Success"
    )
    db_session.add_all([chat_log, agent_log])
    db_session.commit()

    assert chat_log.id is not None
    assert agent_log.id is not None
