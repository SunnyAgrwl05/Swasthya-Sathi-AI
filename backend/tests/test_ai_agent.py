from unittest.mock import patch
import models


def test_chat_endpoint_success(client, db_session):
    """Test /api/chat records conversation logs and returns mocked agent response."""
    mock_reply = "नमस्ते! आज की उपस्थिति दर्ज कर ली गई है।"
    mock_actions = ["mark_attendance(ASHA-PAT-001, present)"]

    with patch("main.chat_with_agent", return_value=(mock_reply, mock_actions)):
        payload = {"message": "Sunita Devi ko present mark karo"}
        response = client.post("/api/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == mock_reply
    assert data["actions_taken"] == mock_actions

    # Verify ChatLog entries: 1 user, 1 agent
    chat_logs = db_session.query(models.ChatLog).all()
    assert len(chat_logs) == 2
    assert chat_logs[0].role == "user"
    assert chat_logs[0].message == "Sunita Devi ko present mark karo"
    assert chat_logs[1].role == "agent"
    assert chat_logs[1].message == mock_reply

    # Verify AgentLog entry
    agent_logs = db_session.query(models.AgentLog).all()
    assert len(agent_logs) == 1
    assert agent_logs[0].query == "Sunita Devi ko present mark karo"
    assert agent_logs[0].response == mock_reply
    assert agent_logs[0].status == "Success"
    assert "mark_attendance" in agent_logs[0].tools_used


def test_daily_broadcast_endpoint(client, sample_worker, db_session):
    """Test /api/broadcast/daily generates broadcast and logs notifications."""
    mock_msg = "सुप्रभात स्वास्थ्य साथियों! आज का टीकाकरण अभियान सुबह 9 बजे से शुरू होगा।"

    with patch("main.generate_daily_broadcast", return_value=mock_msg):
        response = client.get("/api/broadcast/daily")

    assert response.status_code == 200
    assert response.json()["message"] == mock_msg

    # Verify notification log
    notifications = db_session.query(models.NotificationLog).all()
    assert len(notifications) == 1
    assert notifications[0].worker_name == sample_worker.name
    assert notifications[0].phone == sample_worker.phone
    assert notifications[0].notification_type == "WhatsApp"
    assert notifications[0].status == "Sent"


def test_weekly_insights_get(client):
    """Test GET /api/insights/weekly returns generated report."""
    mock_report = "साप्ताहिक रिपोर्ट: 95% उपस्थिति दर्ज की गई।"

    with patch("main.generate_weekly_insights", return_value=mock_report):
        response = client.get("/api/insights/weekly?language=hi")

    assert response.status_code == 200
    assert response.json()["report"] == mock_report


def test_weekly_insights_post(client):
    """Test POST /api/insights/weekly with language parameter."""
    mock_report = "Weekly Report: 95% overall attendance recorded."

    with patch("main.generate_weekly_insights", return_value=mock_report):
        response = client.post("/api/insights/weekly", json={"language": "en"})

    assert response.status_code == 200
    assert response.json()["report"] == mock_report
