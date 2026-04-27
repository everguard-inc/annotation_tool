import pytest

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError
from annotation_tool.infrastructure.api_client import ApiClient


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_api_client_get_projects_filters_unassigned_projects(monkeypatch) -> None:
    """Covers FR-176, FR-177, FR-178."""

    def fake_post(url, json, timeout):
        assert url == "https://api.example.com/api/annotation/projects_data/"
        assert json == {"user_token": "token"}
        return FakeResponse(
            200,
            {
                "projects": [
                    {
                        "id": 1,
                        "uid": "uid-1",
                        "annotation_stage": "ANNOTATE",
                        "annotation_mode": "OBJECT_DETECTION",
                        "assigned_to_user": True,
                    },
                    {
                        "id": 2,
                        "uid": "uid-2",
                        "annotation_stage": "REVIEW",
                        "annotation_mode": "SEGMENTATION",
                        "assigned_to_user": False,
                    },
                ]
            },
        )

    monkeypatch.setattr(
        "annotation_tool.infrastructure.api_client.requests.post", fake_post
    )

    projects = ApiClient("https://api.example.com", "token").get_projects()

    assert len(projects) == 1
    assert projects[0].id == 1
    assert projects[0].stage is AnnotationStage.ANNOTATE
    assert projects[0].mode is AnnotationMode.OBJECT_DETECTION


def test_api_client_raises_backend_error_on_non_200(monkeypatch) -> None:
    """Covers FR-032."""

    def fake_post(url, json, timeout):
        return FakeResponse(500, {"error": "server exploded"})

    monkeypatch.setattr(
        "annotation_tool.infrastructure.api_client.requests.post", fake_post
    )

    with pytest.raises(BackendError, match="Backend error 500"):
        ApiClient("https://api.example.com", "token").complete_task("project-uid", 1.5)
