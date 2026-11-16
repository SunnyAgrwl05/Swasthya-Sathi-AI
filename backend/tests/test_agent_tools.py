"""
Unit tests for AI Agent local tool calling and bilingual dispatching (Issue #24)
---------------------------------------------------------------------------------
Validates that local environment executes database-backed attendance tools
instead of behaving as a generic conversational chatbot.
"""

from fastapi.testclient import TestClient

from agent import chat_with_agent
from main import app

client = TestClient(app)


def test_local_tool_fallback_lowest_attendance():
    """Validates the exact issue query: 'Is month sabse kam attendance kiski hai?'"""
    reply, actions = chat_with_agent("Is month sabse kam attendance kiski hai?")
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert "Attendance" in reply or "Worker" in reply or "Recommendation" in reply
    assert len(actions) > 0


def test_local_tool_fallback_who_has_not_marked():
    """Validates pending attendance query in Hinglish: 'Aaj kis kis ka attendance nahi laga hai?'"""
    reply, actions = chat_with_agent("Aaj kis kis ka attendance nahi laga hai?")
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert "Daily Operations Report" in reply or "Attendance" in reply or "Recommendation" in reply


def test_local_tool_fallback_list_workers():
    """Validates roster listing command: 'List all health workers'"""
    reply, actions = chat_with_agent("List all health workers")
    assert isinstance(reply, str)
    assert len(reply) > 0


def test_local_tool_fallback_daily_broadcast():
    """Validates daily broadcast generation command"""
    reply, actions = chat_with_agent("Aaj ka daily attendance broadcast update banao")
    assert isinstance(reply, str)
    assert len(reply) > 0


def test_local_tool_fallback_weekly_insights():
    """Validates weekly insights command"""
    reply, actions = chat_with_agent("Pichhle hafte ka weekly attendance insights report do")
    assert isinstance(reply, str)
    assert len(reply) > 0


def test_chat_api_endpoint_execution():
    """Validates the FastAPI POST /api/chat endpoint with an operational query"""
    response = client.post("/api/chat", json={"message": "Is month sabse kam attendance kiski hai?"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "actions_taken" in data
    assert len(data["reply"]) > 0
