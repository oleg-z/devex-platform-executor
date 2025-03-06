import dataclasses
from typing import Dict, List, Optional
from base_api import BaseAPI

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Deployment:
    id: UUID = ""
    application_id: UUID = ""
    configuration_id: UUID = ""
    configuration_version: str = ""
    state: str = "pending"
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    def as_dict(self):
        return dataclasses.asdict(self)


class DeploymentService(BaseAPI):
    def __init__(self, session):
        super().__init__(session)
        self.service_url = f"{session.api_base_url}/deployments"

    def create(self, data: Dict[str, Dict[str, str]]) -> bool:
        return self.create()

    def get(self, deployment_id: int) -> Deployment:
        return self.deployment_repository.get_deployment(deployment_id)

    def get_all(self) -> List[Deployment]:
        all_data = super().get_all()
        return [Deployment(**data) for data in all_data]

    def delete(self, deployment_id: int) -> None:
        return self.deployment_repository.delete_deployment(deployment_id)
