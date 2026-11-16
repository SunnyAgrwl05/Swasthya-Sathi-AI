from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_analytics_summary_includes_trends():
    response = client.get("/api/analytics/summary?days=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "attendance_pct" in item
        assert "trend" in item
        assert item["trend"] in ("up", "down", "flat")
        assert "change_pct" in item
        assert "this_week_pct" in item
        assert "last_week_pct" in item
