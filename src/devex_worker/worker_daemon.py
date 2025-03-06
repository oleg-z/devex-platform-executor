from functools import cached_property
from pathlib import Path
import threading
from typing import Optional
import yaml
from loguru import logger
import time
from uuid import uuid4

from deployment_execution import DeploymentExecution
from services.application_service import Application, ApplicationService
from services.configuration_service import Configuration, ConfigurationService
from services.deployment_service import DeploymentService, Deployment
from session import Session


class WorkerDaemon:
    @staticmethod
    def start():
        deployment_service = DeploymentService(session=Session.load_session())
        active_threads = []
        max_threads = 3

        scheduled_deployments = []
        while True:
            pending_deployments = [d for d in deployment_service.get_all() if d.state == "pending"]

            for deployment in pending_deployments:
                if deployment.id in scheduled_deployments:
                    continue

                if len(active_threads) > max_threads:
                    continue

                logger.info(f"Scheduling deployment: {deployment.id}")
                t = threading.Thread(target=WorkerDaemon(deployment=deployment).run)
                t.start()
                active_threads.append(t)
                scheduled_deployments.append(deployment.id)

            active_threads = [t for t in active_threads if t.is_alive()]
            time.sleep(10)

    def __init__(self, deployment: Deployment = None, application_file: str = None, configuration_file: str = None):
        self.plugins = {}

        self.configuration: Optional[Configuration] = None
        self.application: Optional[Application] = None

        self.local_run = False
        if deployment:
            self.deployment = deployment
        else:
            self.local_run = True
            self.deployment = Deployment()
            self.deployment.id = uuid4()

            self.application_file = application_file
            self.configuration_file = configuration_file

    @cached_property
    def configuration_service(self):
        return ConfigurationService(session=Session.load_session())

    @cached_property
    def application_service(self):
        return ApplicationService(session=Session.load_session())

    @cached_property
    def deployment_service(self):
        return DeploymentService(session=Session.load_session())

    def load_data_from_api(self):
        self.configuration = self.configuration_service.get(self.deployment.configuration_id)
        self.application = self.application_service.get(self.deployment.application_id)

    def load_data_from_local(self):
        self.application = Application(id=uuid4(), name="local")
        self.application.definition = self._parse_yaml(self.application_file)

        self.configuration = Configuration()
        self.configuration.definition = self._parse_yaml(self.configuration_file)

    def load_plugins(self):
        """Dynamically load plugins for different kinds of resources."""
        plugins_dir = Path(__file__).parent / "plugins"
        if not plugins_dir.exists():
            logger.error(f"Warning: No plugins found")
            return

        for resource in self.application.resources:
            kind = resource["kind"]  # Convert kind to valid module name
            if kind in self.plugins:
                continue

            entrypoint_path = plugins_dir / kind / "plugin.sh"
            if entrypoint_path.exists():
                self.plugins[resource["kind"]] = entrypoint_path
            else:
                logger.error(f"Warning: No plugin found for {kind}, skipping...")

    def run(self, plan_only=False):
        """Worker function to process resources from the queue."""

        logger.info(f"[{self.deployment.id}] Processing deployment...")
        deployment_status = None
        try:
            if not self.local_run:
                self.load_data_from_api()
            else:
                self.load_data_from_local()

            self.load_plugins()

            worker_deployment = DeploymentExecution(
                plugins=self.plugins,
                deployment=self.deployment,
                application=self.application,
                configuration=self.configuration,
                plan_only=plan_only,
            )
            worker_deployment.merge_definition_and_configuration()
            worker_deployment.run()

            deployment_status = worker_deployment.deployment_status
        except Exception as exc:
            logger.exception(exc)
            deployment_status = "failed"
        finally:
            logger.info(f"[{self.deployment.id}] Updating deployment status to '{deployment_status}'")
            if not self.local_run:
                self.deployment.state = deployment_status
                self.deployment_service.update(self.deployment.id, self.deployment.as_dict())

    def _parse_yaml(self, file_path):
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
