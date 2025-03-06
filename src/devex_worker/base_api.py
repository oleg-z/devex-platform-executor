from typing import Any, Dict, List, Optional
from loguru import logger
import requests

from session import Session


class BaseAPI:
    """Base class to interact with CRUD API services."""

    def __init__(self, session: Session):
        self.token = session.token
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.service_url = ""

    def get_all(self) -> Optional[List[Dict[str, Dict[str, Any]]]]:
        response = requests.get(f"{self.service_url}", headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def get(self, id) -> Optional[Dict[str, Dict[str, Any]]]:
        response = requests.get(f"{self.service_url}/{id}", headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def create(self, id, data) -> Optional[Dict[str, Dict[str, Any]]]:
        response = requests.post(f"{self.service_url}", json=data, headers=self.headers)
        return response.json() if response.status_code in [200, 201] else None

    def update(self, id, data) -> Optional[Dict[str, Dict[str, Any]]]:
        response = requests.put(f"{self.service_url}/{id}/", json=data, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"Failed to update {self.service_url}/{id}/. Status code: {response.status_code}. Response: {response.text}"
            )

    def delete(self, id) -> bool:
        response = requests.delete(f"{self.service_url}/{id}", headers=self.headers)
        return response.status_code == 204
