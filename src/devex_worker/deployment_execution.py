import copy
from functools import cached_property
from pathlib import Path
from queue import Queue
import time
from loguru import logger
import yaml
import re
from services.application_service import Application
from services.configuration_service import Configuration
from services.deployment_service import Deployment
from plugin_executor import PluginExecutor


class DeploymentExecution:
    def __init__(self, plugins, application, configuration, deployment, plan_only):
        self.plugins = plugins
        self.deployment: Deployment = deployment
        self.application: Application = application
        self.configuration: Configuration = configuration
        self.plan_only = plan_only

        self.queue = Queue()
        self.resource_data = {}
        self.resource_deployment_status = {}
        self.execution_stdout = []
        self.execution_stderr = []

    @cached_property
    def tmp_folder(self) -> Path:
        tmp_path = Path().cwd() / f".devex-runner/executions/{self.deployment.id}"
        tmp_path.mkdir(parents=True, exist_ok=True)
        return tmp_path

    @property
    def deployment_status(self):
        for resource_status in self.resource_deployment_status.values():
            if resource_status["status"] == "FAILED":
                return "failed"

            if resource_status["status"] == "PENDING":
                return "pending"

        return "deployed"

    def merge_definition_and_configuration(self):
        """Merge the application definition and configuration."""
        definition_as_string = yaml.dump(self.application.definition)
        for key, value in self.configuration.definition["config"].items():
            definition_as_string = definition_as_string.replace(f"${{{key}}}", value)
        self.application.definition = yaml.safe_load(definition_as_string)

    def run(self):
        for resource in self.application.resources:
            self.resource_deployment_status[resource["name"]] = {"status": "PENDING"}
            self.queue.put(resource)

        while not self.queue.empty():
            resource = self.queue.get()
            self.process_resource(resource)
            self.queue.task_done()

    def process_resource(self, resource):
        """Process a resource using its respective plugin."""
        plugin_script = self.plugins.get(resource["kind"])
        resource_name = resource["name"]

        self.resource_data[resource_name] = copy.deepcopy(resource)

        if not plugin_script:
            self.resource_deployment_status[resource_name] = {
                "status": "FAILED",
                "reason": "Dependent resource failed to deploy",
            }
            return

        if self.resolve_dependencies(resource) is False:
            self.resource_deployment_status[resource_name] = {
                "status": "FAILED",
                "reason": "Dependent resource failed to deploy",
            }
            logger.error(f"Failed to process resource: {resource_name}. Reason: Dependent resource failed to deploy")
            return

        resource_yaml_path = self.tmp_folder / "resource.yaml"
        logger.info(f"Writing resource yaml to {resource_yaml_path}")
        resource_yaml = self.resolve_references(resource)
        resource_yaml_path.write_text(yaml.dump(resource_yaml))

        try:
            plugin = PluginExecutor(plugin_script, workdir=self.tmp_folder)
            with plugin.plan() as process:
                for line in process.read_stdout():
                    print(line)

            if self.plan_only is False:
                with plugin.deploy() as process:
                    for line in process.read_stdout():
                        print(line)

                self.resource_data[resource_name]["output"] = plugin.output()

            self.resource_deployment_status[resource_name] = {
                "status": "DEPLOYED",
                "reason": "Resource deployed successfully",
            }
        except Exception as exception:
            self.resource_deployment_status[resource_name] = {
                "status": "FAILED",
                "reason": "Failed to process resource",
                "stacktrace": exception,
            }
            logger.exception(f"[{resource_name}] Failed to process resource", exception)

    def resolve_dependencies(self, resource) -> bool:
        """Ensure all dependencies are resolved before processing a resource. Return true if resource is ready to be processed"""

        depends_on = resource.get("depends_on", [])
        unresolved_dependencies = depends_on.copy()
        while unresolved_dependencies:
            for dep in unresolved_dependencies:
                dependency_status = self.resource_deployment_status.get(dep, {"status": "PENDING"})["status"]
                self.resource_deployment_status.get(dep)
                if dependency_status == "DEPLOYED":
                    unresolved_dependencies.remove(dep)
                if dependency_status == "FAILED":
                    return False
                else:
                    print(f"Waiting for dependency '{dep}' to be resolved...")
                    time.sleep(0.1)

        return True

    def resolve_references(self, resource):
        """Replace placeholders in resource properties with resolved outputs."""

        items = {}
        if isinstance(resource, list):
            items = dict(enumerate(resource)).items()
        elif isinstance(resource, dict):
            items = resource.items()

        for key, value in items:
            if isinstance(value, list) or isinstance(value, dict):
                self.resolve_references(value)
                continue

            if not isinstance(value, str):
                continue

            for item in re.findall(r"\$\{(.*?)\}", value):
                try:
                    resource_name, section, field_name = item.split(".", 2)
                    resource[key] = value.replace(
                        f"${{{item}}}", self.resource_data[resource_name][section][field_name]
                    )
                except ValueError as exc:
                    raise Exception(f"Failed to resolve dependency '{item}'") from exc
                except KeyError as exc:
                    raise Exception(f"Failed to resolve dependency '{item}'") from exc

        return resource
