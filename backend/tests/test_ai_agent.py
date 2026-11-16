from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
import models


def test_chat_endpoint_with_mocked_agent(client, db_session):
    mock_reply = "Aapka attendance mark kar diya gaya hai."
    mock_actions = ["mark_worker_attendance"]

    with patch("main.chat_with_agent", return_value=(mock_reply, mock_actions)) as mock_agent:
        res = client.post("/api/chat", json={"message": "Mark attendance for Sunny"})
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == mock_reply
        assert data["actions_taken"] == mock_actions
        mock_agent.assert_called_once_with("Mark attendance for Sunny")

    # Verify log entry created in DB
    chat_logs = db_session.query(models.ChatLog).all()
    assert len(chat_logs) >= 2  # user and agent
    agent_logs = db_session.query(models.AgentLog).all()
    assert len(agent_logs) >= 1
    assert agent_logs[-1].status == "Success"


def test_broadcast_and_weekly_insights_endpoints(client, db_session):
    w = models.HealthWorker(worker_code="B1", name="Worker B", center="CB", phone="9990001112")
    db_session.add(w)
    db_session.commit()

    with patch("main.generate_daily_broadcast", return_value="Aaj ki daily report") as mock_broad:
        res = client.get("/api/broadcast/daily")
        assert res.status_code == 200
        assert res.json()["message"] == "Aaj ki daily report"
        mock_broad.assert_called_once()

    with patch("main.generate_weekly_insights", return_value="Weekly insight summary") as mock_insight:
        res_get = client.get("/api/insights/weekly?language=hi")
        assert res_get.status_code == 200
        assert res_get.json()["report"] == "Weekly insight summary"

        res_post = client.post("/api/insights/weekly", json={"language": "en"})
        assert res_post.status_code == 200
        assert res_post.json()["report"] == "Weekly insight summary"
