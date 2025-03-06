from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
import requests
import yaml

from base_api import BaseAPI
from session import Session


def load_yaml(self):
    """Load and parse the YAML file."""
    with open(self.yaml_file, "r") as file:
        data = yaml.safe_load(file)
        self.resources = data.get("spec", [])


@dataclass
class Application:
    id: UUID
    name: str
    definition: str = ""
    version: str = ""

    def __post_init__(self):
        self.definition = yaml.safe_load(self.definition)

    @property
    def resources(self):
        return self.definition["resources"]

    @property
    def metadata(self):
        return self.definition["metadata"]


class ApplicationService(BaseAPI):
    """Class to interact with the Applications API."""

    def __init__(self, session: Session):
        super().__init__(session)
        self.service_url = f"{session.api_base_url}/applications"

    def get_all(self) -> List[Application]:
        all_data = super().get_all()
        return [Application(**data) for data in all_data] if all_data else []

    def get(self, id) -> Optional[Application]:
        data = super().get(id)
        return Application(**data) if data else None

    def create(self, data):
        response = super().create(data)
        return response.json() if response.status_code == 201 else None

    def update(self, id, data):
        response = super.update(id, data)
        return response.json() if response.status_code == 200 else None
