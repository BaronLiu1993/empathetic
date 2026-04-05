import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestProcessEndpoint:
    @patch("router.analysis_router.process_brain_analysis")
    def test_queues_task(self, mock_task, client):
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_task.delay.return_value = mock_result

        response = client.post(
            "/v1/api/analysis/process",
            json={"html": "<p>hello</p>", "user_id": "user1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["task_id"] == "task-123"
        mock_task.delay.assert_called_once_with("<p>hello</p>", "user1")

    @patch("router.analysis_router.process_brain_analysis")
    def test_returns_500_on_error(self, mock_task, client):
        mock_task.delay.side_effect = RuntimeError("rabbitmq down")

        response = client.post(
            "/v1/api/analysis/process",
            json={"html": "<p>hello</p>", "user_id": "user1"},
        )

        assert response.status_code == 500

    def test_missing_fields_returns_422(self, client):
        response = client.post(
            "/v1/api/analysis/process",
            json={"html": "<p>hello</p>"},
        )

        assert response.status_code == 422
