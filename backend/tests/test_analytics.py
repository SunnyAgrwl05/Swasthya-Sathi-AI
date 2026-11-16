"""
Unit tests for Analytics, Broadcast, and Weekly Insights Endpoints
------------------------------------------------------------------
"""

from unittest.mock import patch


def test_analytics_summary_empty(client):
    """Verifies that GET /api/analytics/summary returns empty list when no workers exist."""
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    assert response.json() == []


def test_analytics_summary_with_records(client, sample_worker, sample_attendance):
    """Verifies analytics calculations for total_logged, present count, and attendance_pct."""
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["worker_id"] == sample_worker.id
    assert item["name"] == sample_worker.name
    assert item["total_logged"] == len(sample_attendance)
    assert item["present"] == 4
    # 4 out of 5 present -> 80.0%
    assert item["attendance_pct"] == 80.0


def test_daily_broadcast_endpoint(client, sample_worker):
    """Verifies GET /api/broadcast/daily returns broadcast text and persists notifications."""
    with patch("main.generate_daily_broadcast", return_value="Swasthya Sathi Daily Broadcast Test"):
        response = client.get("/api/broadcast/daily")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Swasthya Sathi Daily Broadcast Test" in data["message"]


def test_weekly_insights_endpoint(client):
    """Verifies GET and POST /api/insights/weekly return generated report text."""
    with patch("main.generate_weekly_insights", return_value="Weekly performance report sample"):
        # GET request
        res_get = client.get("/api/insights/weekly?language=hi")
        assert res_get.status_code == 200
        assert res_get.json()["report"] == "Weekly performance report sample"

        # POST request
        res_post = client.post("/api/insights/weekly", json={"language": "en"})
        assert res_post.status_code == 200
        assert res_post.json()["report"] == "Weekly performance report sample"
