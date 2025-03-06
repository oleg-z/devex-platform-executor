from typing import Dict, List, Optional

import yaml
from base_api import BaseAPI

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Configuration:
    id: UUID = field(default_factory=uuid4)
    application_id: UUID = field(default_factory=uuid4)
    name: str = ""
    definition: str = ""
    version: str = ""
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    def __post_init__(self):
        self.definition = yaml.safe_load(self.definition)


class ConfigurationService(BaseAPI):
    def __init__(self, session):
        super().__init__(session)
        self.service_url = f"{session.api_base_url}/configurations"

    def get(self, id: str, version: Optional[str] = None) -> Configuration:
        data = super().get(id)
        return Configuration(**data)

    def get_all(self) -> List[Configuration]:
        all_data = super().get_all()
        return [Configuration(**data) for data in all_data]
