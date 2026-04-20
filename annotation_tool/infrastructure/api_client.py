from typing import Any

import requests

from annotation_tool.core.enums import AnnotationMode, AnnotationStage
from annotation_tool.core.exceptions import BackendError
from annotation_tool.core.models import ProjectData


class ApiClient:
    def __init__(self, api_url: str, token: str, timeout_seconds: int = 10) -> None:
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def get_projects(self, only_assigned_to_user: bool = True) -> list[ProjectData]:
        url = f"{self.api_url}/api/annotation/projects_data/"
        data = {"user_token": self.token}

        response = self._post(url, data)
        projects = response.get("projects", [])

        result: list[ProjectData] = []
        for project in projects:
            if only_assigned_to_user and not project.get("assigned_to_user", True):
                continue
            result.append(ProjectData.from_dict(project))

        return result

    def get_project_data(self, project_uid: str) -> tuple[AnnotationStage, AnnotationMode]:
        url = f"{self.api_url}/api/annotation/get_project_data/{project_uid}/"
        response = self._post(url, {"user_token": self.token})

        return (
            AnnotationStage[response["annotation_stage"]],
            AnnotationMode[response["annotation_mode"]],
        )

    def complete_task(self, project_uid: str, duration_hours: float) -> None:
        url = f"{self.api_url}/api/annotation/complete_task/{project_uid}/"
        self._post(url, {"user_token": self.token, "duration_hours": duration_hours})

    def is_available(self) -> bool:
        try:
            requests.get(self.api_url, timeout=3)
            return True
        except requests.RequestException:
            return False

    def _post(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(url, json=data, timeout=self.timeout_seconds)
        except requests.RequestException as error:
            raise BackendError(f"Unable to reach backend: {error}") from error

        if response.status_code != 200:
            raise BackendError(self._error_message(response))

        try:
            return response.json()
        except ValueError as error:
            raise BackendError("Backend returned invalid JSON.") from error

    def _error_message(self, response: requests.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            body = response.text

        return f"Backend error {response.status_code}: {body}"
