from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
from subprocess import Popen
from typing import Optional
from loguru import logger


class PluginExecutor:
    def __init__(self, entrypoint, workdir):
        self.entrypoint = str(entrypoint)
        self.process: Optional[Popen] = None
        self.workdir = workdir
        self.stdout = None
        self.stderr = None
        self.env = {"PLUGIN_DIR": Path(self.entrypoint).parent.as_posix()}
        self.env.update(os.environ)

    @property
    def resource_yaml_path(self) -> str:
        return str((Path(self.workdir) / "resource.yaml").absolute())

    @contextmanager
    def plan(self):
        logger.info("Running 'plan' stage")
        self.start([self.entrypoint, "plan", self.resource_yaml_path])
        yield self
        self.wait()
        logger.info("Completed 'plan' stage")

    @contextmanager
    def deploy(self):
        logger.info("Running 'deploy' stage")
        self.start([self.entrypoint, "deploy", self.resource_yaml_path])
        yield self
        self.wait()
        logger.info("Completed 'deploy' stage")

    def start(self, command):
        logger.info(f"Running command: {' '.join(command)}")
        self.process = Popen(
            command,
            cwd=self.workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=self.env,
        )

    def read_stdout(self):
        for line in iter(self.process.stdout.readline, b""):
            yield line.decode("utf-8").strip()

    def wait(self):
        self.stdout, self.stderr = self.process.communicate()
        if self.process.returncode != 0:
            raise Exception(f"Command failed with exit code {self.process.returncode}")
