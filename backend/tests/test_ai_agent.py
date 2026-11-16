"""
Unit tests for AI Agent Chat Endpoint (/api/chat)
--------------------------------------------------
Tests agent query handling, audit logging, and mocked LLM execution.
"""

from unittest.mock import patch
import models


def test_chat_endpoint_mocked_success(client, db_session):
    """Verifies that POST /api/chat invokes the agent and records audit logs."""
    mock_reply = "✅ Attendance Updated: Sunita Devi marked Present."
    mock_actions = ["mark_attendance: Sunita Devi"]

    with patch("main.chat_with_agent", return_value=(mock_reply, mock_actions)):
        response = client.post("/api/chat", json={"message": "Sunita Devi ko present mark karo"})
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == mock_reply
        assert data["actions_taken"] == mock_actions

        # Verify database logs were created
        chat_logs = db_session.query(models.ChatLog).all()
        assert len(chat_logs) >= 2  # user message and agent reply
        user_log = [log for log in chat_logs if log.role == "user"][0]
        assert user_log.message == "Sunita Devi ko present mark karo"

        agent_logs = db_session.query(models.AgentLog).all()
        assert len(agent_logs) == 1
        assert agent_logs[0].status == "Success"
        assert agent_logs[0].tools_used == "mark_attendance: Sunita Devi"


def test_chat_endpoint_invalid_payload(client):
    """Verifies that missing message body in chat request returns 422."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
