import hashlib
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime

from lib.common.abstracts import Auxiliary
from lib.common.exceptions import CuckooPackageError
from lib.common.results import upload_to_host

# Set up logging
log = logging.getLogger(__name__)

__author__ = "jonisworking,theoleecj2"
__version__ = "1.0.0"

# Constants for Docker configuration
DOCKER_LOG_NAME = "tracee.data"
DOCKER_CONTAINER_NAME = "tracee"  # Name of the Docker container to monitor
TRACEE_VERSION = "0.24.1"


def is_docker_installed() -> bool:
    """
    Check if Docker is installed on the system.
    """
    return shutil.which("docker") is not None


def is_docker_container_running(container_name):
    """
    Check if the Docker container is currently running.
    """
    try:
        # Check if the container is running
        completed_process = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name], capture_output=True, text=True
        )
        return completed_process.stdout.strip() == "true"
    except Exception as e:
        log.error(f"Error checking container status: {e}")
        return False


def start_docker_container(container_name, tracee_version):
    """
    Start the Docker container.
    """
    try:
        subprocess.run(f"sudo -n docker rm -f {container_name}", shell=True, capture_output=True, timeout=30)
        # Checks
        tracee_cmd = (
            "sudo -n docker run --name tracee --pull=never --log-driver=json-file -d --pid=host --cgroupns=host --privileged "
            + f"-v /etc/os-release:/etc/os-release-host:ro -v {os.getcwd()}/tracee-artifacts/:/tmp/tracee/out/host -v /var/run:/var/run:ro -v {os.getcwd()}/modules/auxiliary/tracee:/policy "
            + "-v /boot:/boot:ro "
            + "-v /sys/kernel/debug:/sys/kernel/debug:ro "
            + "-v /sys/kernel/tracing:/sys/kernel/debug/tracing:ro "
            + f"aquasec/tracee:{tracee_version} --output json --output option:parse-arguments,exec-env,exec-hash --policy /policy/policy.yml "
            + "--capture bpf --capture module --capture exec"
        )

        log.debug(tracee_cmd)

        # Run Docker cmd to start the container
        result = subprocess.run(
            tracee_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        result.check_returncode()
        log.debug(f"Docker container started: {result.stdout}")

        # Health check to wait until Tracee begins recording events
        health_check_failed = True
        deadline = time.monotonic() + 300

        while health_check_failed and time.monotonic() < deadline:
            time.sleep(10)
            result = subprocess.run("strace echo tracee-health-check-1903ae", shell=True, capture_output=True, text=True, timeout=15)
            log.info(result.stdout)
            health_check_log = subprocess.run("sudo -n docker logs tracee", shell=True, capture_output=True, text=True, timeout=15)
            health_check_log.check_returncode()
            log.info(health_check_log.stdout)
            if "1903ae" in health_check_log.stdout:
                health_check_failed = False
            elif not is_docker_container_running(container_name):
                raise CuckooPackageError(
                    "Tracee stopped before readiness: " + (health_check_log.stdout + health_check_log.stderr)[-4000:]
                )
        if health_check_failed:
            raise CuckooPackageError("Tracee did not produce the health-check event within 300 seconds")

    except subprocess.CalledProcessError as e:
        raise CuckooPackageError(f"Cannot start Tracee: {e.stderr}") from e


def stop_docker_container(container_name):
    """
    Stop the Docker container.
    """
    try:
        # Run the Docker command to stop the container
        result = subprocess.run(["sudo", "-n", "docker", "stop", container_name], check=True, capture_output=True, text=True, timeout=45)
        log.debug(f"Docker container stopped: {result.stdout}")

    except subprocess.CalledProcessError as e:
        raise CuckooPackageError(f"Cannot stop Tracee: {e.stderr}") from e


class Docker(Auxiliary):
    """
    Class for managing Docker operations.
    """

    def __init__(self, options, config):
        """
        Initialize Docker instance.
        """
        log.info("docker start")
        self.enabled = config.tracee_linux
        log.info(self.enabled)
        log.info("Tracee")
        Auxiliary.__init__(self, options, config)
        self.start_time = None
        self.end_time = None

    def start(self):
        """
        Start Docker container.
        """
        if not self.enabled:
            return False  # result.stdout

        if not is_docker_installed():
            raise CuckooPackageError("Your VM needs to have Docker installed in order to use Docker functionality (tracee).")

        # Check if the Docker container is already running
        if not is_docker_container_running(DOCKER_CONTAINER_NAME):
            # Start Docker container if it's not running
            log.debug("Starting docker container")
            start_docker_container(DOCKER_CONTAINER_NAME, TRACEE_VERSION)
        else:
            log.debug("Docker container is already running.")

        self.start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def collect_logs(self):
        """
        Collect Docker container logs.
        """

        result = subprocess.run(
            ["sudo", "-n", "docker", "inspect", "--format", "{{.LogPath}}", DOCKER_CONTAINER_NAME],
            check=True, capture_output=True, text=True, timeout=30,
        )
        # Keep Docker's JSON envelope: the Community processor expects it.
        upload_to_host(result.stdout.strip(), "logs/tracee.log")
        
        artifacts_dir = os.path.join(os.getcwd(), "tracee-artifacts")
        if os.path.islink(artifacts_dir):
            log.warning("Skipping symlinked Tracee artifacts directory: %s", artifacts_dir)
            return

        for directory, _, filenames in os.walk(artifacts_dir):
            for filename in filenames:
                file_path = os.path.join(directory, filename)
                if os.path.islink(file_path) or not os.path.isfile(file_path):
                    continue
                with open(file_path, "rb") as artifact:
                    digest = hashlib.file_digest(artifact, "sha256").hexdigest()
                upload_to_host(file_path, f"tracee/{digest}", category="tracee")

    def stop(self) -> bool:
        """
        Stop Docker container.
        """
        log.debug("Tracee module instructed to stop")
        if self.enabled:
            log.debug("Tracee module instructed to stop + was enabled")
            self.end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            # Stop the Docker container
            stop_docker_container(DOCKER_CONTAINER_NAME)
            self.collect_logs()

            return True
        return False
