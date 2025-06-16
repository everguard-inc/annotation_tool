from typing import List

import requests

from config import settings
from exceptions import MessageBoxException
from models import ProjectData


def get_headers():
    return {'Authorization': f'Token {settings.token}'}


def load_public_key():
    url = f"{settings.api_url}/api/v2/annotation/public_key/"
    response = requests.get(url=url, headers=get_headers())
    if response.status_code == 200:
        return response.json()["public_key"]
    raise MessageBoxException(f"Internal Server Error with connection to portal.")


def get_projects_data(only_assigned_to_user: bool = True) -> List[ProjectData]:
    url = f'{settings.api_url}/api/v2/annotation/tasks/'

    response = requests.get(url=url, headers=get_headers())

    if response.status_code == 200:
        projects = response.json()["projects"]

        result = list()
        for project in projects:
            if only_assigned_to_user and not project.get("assigned_to_user", True):
                continue
            result.append(ProjectData.from_json(project))
        return result
    
    raise MessageBoxException(f"Unable to get projects data. {response.status_code}")


def complete_task(project_uid: int, duration_hours: float):
    url = f'{settings.api_url}/api/annotation/tasks/{project_uid}/complete/' # Change stage of annotation project

    data = {'duration_hours': duration_hours}
    response = requests.post(url=url, headers=get_headers(), json=data)

    if response.status_code != 200:
        try: 
            message = response.json()
        except Exception as e:
            message = f"Internal Server Error with project uid {project_uid}"
        raise MessageBoxException(message)
