from functools import cached_property
import json
from pathlib import Path
import time
from jinja2 import Template
import subprocess

from loguru import logger
import yaml
import argparse


class ResourceHandler:
    KIND = "terraform/aws"
    TEMPLATE_FILE = Path(__file__).parent / "template.tf.j2"

    def __init__(self, resource):
        self.resource = resource

    @cached_property
    def tmp_folder(self) -> Path:
        tmp_path = Path.cwd() / ".plugins/" / ResourceHandler.KIND
        tmp_path.mkdir(parents=True, exist_ok=True)
        return tmp_path

    @cached_property
    def tf_runner(self):
        return ResourceHandler.TerraformRunner(self.tmp_folder)

    def plan(self):
        self.render_terraform_file()
        self.tf_runner.init()
        self.tf_runner.plan()
        return {}

    def deploy(self):
        self.render_terraform_file()
        self.tf_runner.apply()
        return {}

    def render_terraform_file(self):
        with open(ResourceHandler.TEMPLATE_FILE, "r") as f:
            tf_template_content = f.read()
        tf_template = Template(tf_template_content)
        rendered_template = tf_template.render(**self.resource)
        main_tf_content = json.dumps(yaml.safe_load(rendered_template), indent=2)

        temp_dir = Path("/tmp") / f"terraform_module_{int(time.time())}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = self.tmp_folder / "main.tf.json"
        temp_file_path.write_text(main_tf_content)
        print(f"Rendered template written to temporary file: {temp_file_path}")

    class TerraformRunner:
        def __init__(self, working_dir):
            self.working_dir = Path(working_dir)

        def init(self):
            stdout, _ = self._run_terraform_command(["terraform", "init"])
            return stdout

        def plan(self):
            stdout, _ = self._run_terraform_command(["terraform", "plan"])
            return stdout

        def apply(self):
            stdout, _ = self._run_terraform_command(["terraform", "apply", "-auto-approve"])
            return stdout

        def output(self):
            stdout, stderr = self._run_terraform_command(["terraform", "output", "-json"])
            return json.loads(stdout)

        def destroy(self):
            stdout, _ = self._run_terraform_command(["terraform", "destroy", "-auto-approve"])
            return stdout

        def _run_terraform_command(self, command):
            logger.info(f"Running terraform command: {' '.join(command)}")
            process = subprocess.Popen(command, cwd=self.working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for line in iter(process.stdout.readline, b""):
                print(line.decode("utf-8").strip())

            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(f"Terraform command failed: {stderr.decode('utf-8')}")
            return stdout.decode("utf-8"), stderr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terraform Resource Handler")
    parser.add_argument("action", choices=["plan", "deploy", "destroy"], help="Action to perform")
    parser.add_argument("resource", type=str, help="Path to the resource YAML file")

    args = parser.parse_args()

    with open(args.resource, "r") as f:
        resource = yaml.safe_load(f)

    handler = ResourceHandler(resource)

    if args.action == "plan":
        handler.plan()
    elif args.action == "deploy":
        handler.deploy()
    elif args.action == "output":
        print(handler.output())
    elif args.action == "destroy":
        handler.tf_runner.destroy()
