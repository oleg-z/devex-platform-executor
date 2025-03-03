import yaml
import importlib
import threading
import time
import os
from queue import Queue


class WorkerDaemon:
    def __init__(self, definition):
        self.definition = yaml.safe_load(definition)
        self.resources = self.definition.get("spec", [])
        self.queue = Queue()
        self.outputs = {}
        self.plugins = {}
        self.load_plugins()

    def load_yaml(self):
        """Load and parse the YAML file."""
        with open(self.yaml_file, "r") as file:
            data = yaml.safe_load(file)
            self.resources = data.get("spec", [])

    def load_plugins(self):
        """Dynamically load plugins for different kinds of resources."""
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)

        for resource in self.resources:
            kind = resource["kind"].replace("/", ".")  # Convert kind to valid module name
            if kind not in self.plugins:
                try:
                    module = importlib.import_module(f"plugins.{kind}")
                    self.plugins[resource["kind"]] = module.ResourceHandler()
                except ModuleNotFoundError:
                    print(f"Warning: No plugin found for {kind}, skipping...")

    def resolve_dependencies(self, resource):
        """Ensure all dependencies are resolved before processing a resource."""
        depends_on = resource.get("depends_on", [])
        unresolved_dependencies = depends_on.copy()
        while unresolved_dependencies:
            for dep in unresolved_dependencies:
                if dep in self.outputs:
                    unresolved_dependencies.remove(dep)
                else:
                    print(f"Waiting for dependency '{dep}' to be resolved...")
                    time.sleep(5)

    def substitute_env_vars(self, properties):
        """Replace placeholders in resource properties with resolved outputs."""
        for key, value in properties.items():
            if isinstance(value, str) and "${" in value:
                for res_name, output in self.outputs.items():
                    value = value.replace(f"${{{res_name}.output.bucket_name}}", output.get("bucket_name", ""))
                properties[key] = value
        return properties

    def process_resource(self, resource):
        """Process a resource using its respective plugin."""
        handler = self.plugins.get(resource["kind"])
        if handler:
            self.resolve_dependencies(resource)
            resource["properties"] = self.substitute_env_vars(resource["properties"])
            output = handler.apply(resource)
            self.outputs[resource["name"]] = output
        else:
            print(f"Skipping unknown resource: {resource['kind']}")

    def worker(self):
        """Worker function to process resources from the queue."""
        while not self.queue.empty():
            resource = self.queue.get()
            self.process_resource(resource)
            self.queue.task_done()

    def run(self):
        """Start the worker daemon."""
        for resource in self.resources:
            self.queue.put(resource)

        threads = []
        for _ in range(min(5, len(self.resources))):  # Max 5 worker threads
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
