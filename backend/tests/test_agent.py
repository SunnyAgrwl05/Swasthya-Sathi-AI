from fastapi.testclient import TestClient
from main import app
from agent import chat_with_agent

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
