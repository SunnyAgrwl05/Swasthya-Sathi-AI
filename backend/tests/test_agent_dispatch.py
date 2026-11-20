from fastapi.testclient import TestClient

from main import app
from agent import classify_attendance_intent, execute_attendance_intent, chat_with_agent

client = TestClient(app)


def test_classify_low_attendance_hindi():
    intent, params = classify_attendance_intent("Is month sabse kam attendance kiski hai?")
    assert intent == "LOW_ATTENDANCE"
    assert params.get("days") == 30


def test_classify_who_not_marked_today():
    intent, params = classify_attendance_intent("Aaj kisne attendance nahi mark ki?")
    assert intent == "WHO_NOT_MARKED"


def test_classify_mark_attendance_hinglish():
    intent, params = classify_attendance_intent("Sunny Kumar ko aaj present mark karo")
    assert intent == "MARK_ATTENDANCE"
    assert "Sunny" in params.get("worker_name", "")
    assert params.get("status") == "present"


def test_classify_summary_hinglish():
    intent, params = classify_attendance_intent("Kajal Kumari ka attendance summary dikhao")
    assert intent == "ATTENDANCE_SUMMARY"
    assert "Kajal" in params.get("worker_name", "")


def test_classify_daily_broadcast():
    intent, params = classify_attendance_intent("Aaj ka daily broadcast WhatsApp status update bhejo")
    assert intent == "DAILY_BROADCAST"


def test_classify_list_workers():
    intent, params = classify_attendance_intent("Sab workers ki list dikhao")
    assert intent == "LIST_WORKERS"


def test_execute_low_attendance_intent():
    res, actions = execute_attendance_intent("LOW_ATTENDANCE", {"days": 30})
    assert "Attendance Analysis" in res or "No follow-up required" in res
    assert len(actions) > 0


def test_execute_who_not_marked_intent():
    res, actions = execute_attendance_intent("WHO_NOT_MARKED", {})
    assert "Daily Operations Report" in res
    assert len(actions) > 0


def test_chat_with_agent_attendance_offline_fallback():
    # In offline mode / test environment without API keys, attendance intent executes database tool
    reply, actions = chat_with_agent("Is month sabse kam attendance kiski hai?")
    assert "Attendance Analysis" in reply or "No follow-up required" in reply
    assert len(actions) > 0


def test_chat_endpoint():
    response = client.post("/api/chat", json={"message": "Is month sabse kam attendance kiski hai?"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "actions_taken" in data
    assert len(data["actions_taken"]) > 0


def test_chat_stream_endpoint():
    response = client.post("/api/chat/stream", json={"message": "Aaj kisne attendance nahi mark ki?"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "data:" in text
    assert '"type": "chunk"' in text or '"type": "done"' in text
