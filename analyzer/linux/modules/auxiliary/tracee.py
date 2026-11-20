import hashlib
import logging
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from lib.common.abstracts import Auxiliary
from lib.common.constants import ROOT
from lib.common.exceptions import CuckooPackageError
from lib.common.results import upload_to_host

log = logging.getLogger(__name__)

__author__ = "jonisworking,theoleecj2"
__version__ = "1.0.0"

TRACEE = "/opt/tracee/tracee"
SIGNATURES = "/opt/tracee/signatures"
POLICY = Path(__file__).resolve().parent / "tracee" / "policy.yml"


class Tracee(Auxiliary):
    def __init__(self, options, config):
        self.enabled = config.tracee_linux
        super().__init__(options, config)
        self.process = None

    def start(self):
        if not self.enabled:
            return False

        self.run_dir = Path(tempfile.mkdtemp(prefix="cape-tracee-", dir=ROOT))
        self.events = self.run_dir / "tracee.log"
        self.stderr = self.run_dir / "tracee.stderr.log"
        command = [
            "sudo", "-n", TRACEE, "--signatures-dir", SIGNATURES,
            "--policy", str(POLICY), "--output", "json",
            "--output", "option:parse-arguments,exec-env,exec-hash",
            "--capture", "bpf", "--capture", "module", "--capture", "exec",
            "--capture", f"dir:{self.run_dir}", "--log", "debug",
        ]
        with self.events.open("wb") as events, self.stderr.open("wb") as stderr:
            self.process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=events, stderr=stderr, start_new_session=True
            )

        try:
            deadline = time.monotonic() + 300
            with self.stderr.open("rb") as stderr:
                while time.monotonic() < deadline:
                    status = self.process.poll()
                    if status is not None:
                        raise CuckooPackageError(f"Tracee exited before readiness (status {status})")
                    if any(b"Tracee is ready callback" in line for line in stderr):
                        return True
                    time.sleep(0.25)
            raise CuckooPackageError("Tracee did not become ready within 300 seconds")
        except Exception:
            try:
                self._stop_process()
            finally:
                upload_to_host(str(self.stderr), "logs/tracee.stderr.log")
            raise

    def _stop_process(self):
        if self.process.poll() is None:
            # sudo relays signals from its parent to the Tracee command.
            self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(timeout=45)
        except subprocess.TimeoutExpired as exc:
            raise CuckooPackageError("Tracee did not stop within 45 seconds") from exc

    def collect_logs(self):
        integrity = self.run_dir / "tracee-integrity.txt"
        with self.events.open("rb") as events:
            digest = hashlib.file_digest(events, "sha256").hexdigest()
        integrity.write_text(f"{self.events.stat().st_size} {digest}\n")
        upload_to_host(str(integrity), "logs/tracee-integrity.txt")
        upload_to_host(str(self.events), "logs/tracee.log")
        upload_to_host(str(self.stderr), "logs/tracee.stderr.log")
        artifacts_dir = self.run_dir / "out"
        if artifacts_dir.is_symlink():
            log.warning("Skipping symlinked Tracee artifacts directory: %s", artifacts_dir)
            return

        for directory, _, filenames in os.walk(artifacts_dir):
            for filename in filenames:
                file_path = Path(directory) / filename
                if file_path.is_symlink() or not file_path.is_file():
                    continue
                with file_path.open("rb") as artifact:
                    digest = hashlib.file_digest(artifact, "sha256").hexdigest()
                upload_to_host(str(file_path), f"tracee/{digest}", category="tracee")

    def stop(self):
        if self.process is None:
            return False
        self._stop_process()
        self.collect_logs()
        return True
