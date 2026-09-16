from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_parse_rejects_bad_url():
    res = client.post("/api/parse", json={"url": "not-a-url"})
    assert res.status_code == 400
