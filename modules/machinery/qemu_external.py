import logging
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from contextlib import contextmanager

import requests
from sqlalchemy import select

from lib.cuckoo.common.config import Config
from lib.cuckoo.common.constants import CUCKOO_ROOT
from lib.cuckoo.core.data.task import TASK_RUNNING, Task

from lib.cuckoo.common.exceptions import CuckooCriticalError, CuckooMachineError
from lib.cuckoo.common.path_utils import path_exists
from modules.machinery import qemu as cape_qemu


log = logging.getLogger(__name__)


def _mace_network_args(options, network_model="virtio-net-pci"):
    tap = options.get("analysis_tap")
    if not tap:
        return [], None
    bridge = options.get("analysis_bridge")
    mac = options.get("analysis_mac", "")
    state_path = options.get("analysis_lab_state", "")
    if not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,15}", name) for name in (tap, bridge)) or tap == bridge:
        raise CuckooMachineError("Invalid MACE TAP/bridge names")
    if not (
        re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac)
        and not int(mac[:2], 16) & 1
        and int(mac.replace(":", ""), 16)
        and mac.lower() != options.get("mac", "").lower()
    ):
        raise CuckooMachineError("Invalid or duplicate analysis MAC")
    if not isinstance(state_path, str) or not state_path.startswith("/"):
        raise CuckooMachineError("analysis_lab_state must be an absolute path")
    return [
        "-netdev",
        f"tap,id=net1,ifname={tap},script=no,downscript=no,vnet_hdr=off",
        "-device",
        f"{network_model},netdev=net1,mac={mac},romfile=",
    ], "net1"


@contextmanager
def _mace_lab_lock(options):
    arguments, _ = _mace_network_args(options)
    if not arguments:
        yield
        return
    state_path = Path(options["analysis_lab_state"])
    tap, bridge = options["analysis_tap"], options["analysis_bridge"]
    try:
        # The controller creates this file; CAPE only needs read access to lock it.
        with state_path.with_name(".lab.lock").open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = json.loads(state_path.read_text())
            record = state.get("guest_tap", {})
            if state.get("state") not in ("running", "validated-probe") or not state.get("with_guest"):
                raise CuckooMachineError("Start the MACE lab with up --with-guest first")
            if record.get("name") != tap or record.get("uid") != os.geteuid():
                raise CuckooMachineError("MACE TAP name/owner does not match this QEMU process")
            links = {}
            for name in (tap, bridge):
                links[name] = json.loads(
                    subprocess.run(
                        ["ip", "-j", "-d", "link", "show", "dev", name], check=True, capture_output=True, text=True, timeout=5
                    ).stdout
                )[0]
                addresses = json.loads(
                    subprocess.run(
                        ["ip", "-j", "addr", "show", "dev", name], check=True, capture_output=True, text=True, timeout=5
                    ).stdout
                )[0]
                if "UP" not in links[name].get("flags", []) or addresses.get("addr_info"):
                    raise CuckooMachineError("MACE bridge/TAP must be UP without host IP addresses")
                if Path(f"/proc/sys/net/ipv6/conf/{name}/disable_ipv6").read_text().strip() != "1":
                    raise CuckooMachineError("IPv6 must be disabled on the MACE bridge/TAP")
            live = links[tap]
            if (
                live.get("ifindex") != record.get("ifindex")
                or live.get("ifalias") != record.get("alias")
                or live.get("master") != bridge
                or live.get("linkinfo", {}).get("info_kind") != "tun"
                or "LOWER_UP" in live.get("flags", [])
                or links[bridge].get("ifindex") != state.get("bridge_ifindex")
                or links[bridge].get("linkinfo", {}).get("info_kind") != "bridge"
            ):
                raise CuckooMachineError("MACE bridge/TAP identity changed or TAP already in use")
            flags = int(Path(f"/sys/class/net/{tap}/tun_flags").read_text().strip(), 0)
            owner = int(Path(f"/sys/class/net/{tap}/owner").read_text().strip())
            if not flags & 0x2 or not flags & 0x800 or flags & 0x100 or owner != record["uid"]:
                raise CuckooMachineError("Expected an owned, persistent, single-queue TAP")
            yield
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as error:
        raise CuckooMachineError(f"Cannot use the MACE lab: {error}") from error


def _mace_wait_tap(options, process):
    if not options.get("analysis_tap"):
        return
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise CuckooMachineError("QEMU exited before attaching the analysis TAP")
            carrier = Path(f"/sys/class/net/{options['analysis_tap']}/carrier")
            if carrier.read_text().strip() == "1":
                return
            time.sleep(0.1)
        raise CuckooMachineError("QEMU did not attach the analysis TAP within 10 seconds")
    except Exception:
        # Reap the process before releasing the lock: it must not attach later
        # while the controller is already shutting the network down.
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        raise


class QEMUExternal(cape_qemu.QEMU):
    """QEMU guests with per-machine boot settings and traffic capture."""

    module_name = "qemu_external"

    @staticmethod
    def _guest_paths(options, name):
        params = {"imagepath": os.path.dirname(options.image), "vmname": name}
        paths = {
            key: str(options.get(key) or "").format(**params) for key in ("firmware", "firmware_vars", "seed_image", "console_log")
        }
        paths["firmware_vars_runtime"] = ""
        if paths["firmware_vars"]:
            template = options.get("firmware_vars_runtime") or "{imagepath}/firmware_vars_{vmname}.fd"
            paths["firmware_vars_runtime"] = template.format(**params)
        return paths

    @staticmethod
    def _network_device(cmdline):
        for index, argument in enumerate(cmdline[:-1]):
            if argument == "-device" and "netdev=" in cmdline[index + 1]:
                return cmdline[index + 1].split(",", 1)[0]
        raise CuckooMachineError("The QEMU guest profile has no network device")

    def _user_network_args(self, options, network_model):
        network = f"user,id=net0,restrict=on,ipv6=off,hostfwd=tcp:{options.ip}:8000-:8000"
        ssh_port = options.get("ssh_port")
        if ssh_port:
            network += f",hostfwd=tcp:{options.ip}:{ssh_port}-:22"
        if options.get("resultserver_relay"):
            resultserver = Config().resultserver
            guest_ip = options.get("resultserver_ip")
            if not guest_ip:
                raise CuckooMachineError("resultserver_relay requires a guest-visible resultserver_ip")
            guest_port = options.get("resultserver_port") or resultserver.port
            host_ip = resultserver.ip
            if host_ip == "0.0.0.0":
                host_ip = "127.0.0.1"
            socat = options.get("socat_path") or shutil.which("socat")
            if not socat:
                raise CuckooMachineError("socat is required for the result server relay")
            network += f",guestfwd=tcp:{guest_ip}:{guest_port}-cmd:{socat} STDIO TCP4:{host_ip}:{resultserver.port}"
        return ["-netdev", network, "-device", f"{network_model},netdev=net0,mac={{mac}},romfile="]

    def _get_qemu_args(self, vm_options):
        # Use CAPE's existing architecture profiles without changing the shared
        # table. An unspecified architecture uses the ordinary x64 disk guest.
        arch = vm_options.get("arch") or "x64"
        if arch == "default":
            arch = "x64"
        try:
            profile = cape_qemu.QEMU_ARGS[arch]
        except KeyError as error:
            raise CuckooMachineError(f"Unsupported QEMU guest architecture: {arch}") from error
        cmdline = list(profile["cmdline"])
        network_model = self._network_device(cmdline)

        firmware = vm_options.get("firmware")
        if vm_options.get("firmware_vars") and not firmware:
            raise CuckooMachineError("firmware_vars requires firmware")
        if firmware:
            # Firmware boot is an explicit choice for this guest. Kernel-boot
            # profiles remain available, including ARM32 and other architectures.
            if arch not in ("x64", "x86", "arm", "arm64"):
                raise CuckooMachineError(f"Firmware boot is not supported for the {arch} profile")
            disk_model = "virtio-blk-device" if arch == "arm" else "virtio-blk-pci"
            network_model = "virtio-net-device" if arch == "arm" else "virtio-net-pci"
            network_args = []
            for index, argument in enumerate(cmdline[:-1]):
                if argument == "-netdev":
                    network_args = ["-netdev", cmdline[index + 1], "-device", f"{network_model},netdev=net_{{vmname}},mac={{mac}}"]
                    break
            cmdline = [
                cmdline[0],
                "-name",
                "{vmname}",
                "-display",
                "none",
                "-m",
                "{memory}",
                "-drive",
                f"if=pflash,format=raw,readonly=on,file={firmware}",
                "-drive",
                "id=osdisk,if=none,format=qcow2,file={snapshot_path}",
                "-device",
                f"{disk_model},drive=osdisk",
            ]
            if arch in ("arm", "arm64"):
                cmdline += ["-machine", "virt"]
            cmdline += network_args
            if vm_options.get("firmware_vars"):
                runtime_vars = vm_options.get("firmware_vars_runtime") or "{imagepath}/firmware_vars_{vmname}.fd"
                cmdline += ["-drive", f"if=pflash,format=raw,file={runtime_vars}"]

        if vm_options.get("qemu_machine"):
            for flag in ("-M", "-machine"):
                if flag in cmdline:
                    index = cmdline.index(flag)
                    del cmdline[index : index + 2]
            cmdline += ["-machine", vm_options.qemu_machine]
        for option, flag in (("smp", "-smp"), ("accel", "-accel")):
            if vm_options.get(option):
                cmdline += [flag, str(vm_options[option])]
        if vm_options.get("seed_image"):
            disk_model = "virtio-blk-device" if arch == "arm" else "virtio-blk-pci"
            cmdline += [
                "-drive",
                f"id=seed,if=none,format=raw,readonly=on,file={vm_options.seed_image}",
                "-device",
                f"{disk_model},drive=seed",
            ]
        network = vm_options.get("network") or "tap"
        if network not in ("tap", "user"):
            raise CuckooMachineError(f"Unsupported QEMU network mode: {network}")
        if network == "user":
            filtered = []
            index = 0
            while index < len(cmdline):
                argument = cmdline[index]
                if argument == "-netdev" or (argument == "-device" and "netdev=" in cmdline[index + 1]):
                    index += 2
                else:
                    filtered.append(argument)
                    index += 1
            cmdline = filtered + self._user_network_args(vm_options, network_model)
        if vm_options.get("console_log"):
            cmdline += ["-serial", f"file:{vm_options.console_log}"]
        if "-monitor" not in cmdline:
            cmdline += ["-monitor", "stdio"]
        cmdline[0] = vm_options.get("qemu_path") or os.path.join(self.qemu_dir, os.path.basename(cmdline[0]))
        return {"cmdline": cmdline, "params": dict(profile.get("params", {}))}

    def _initialize_check(self):
        manager = self.options.get(self.module_name)
        qemu_path = manager.get("path")

        if not qemu_path or not path_exists(qemu_path):
            raise CuckooCriticalError(f"QEMU binary not found: {qemu_path}")

        self.qemu_dir = os.path.dirname(qemu_path)
        self.qemu_img = os.path.join(self.qemu_dir, "qemu-img")

        if not path_exists(self.qemu_img):
            raise CuckooCriticalError(f"qemu-img not found: {self.qemu_img}")

        for machine_id in manager.get("machines"):
            machine_id = machine_id.strip()
            machine = self.options.get(machine_id)
            image = machine.get("image")

            if not image or not path_exists(image):
                raise CuckooCriticalError(f"Golden image not found for {machine_id}: {image}")

            try:
                profile = self._get_qemu_args(machine)
                paths = self._guest_paths(machine, machine_id)
            except CuckooMachineError as error:
                raise CuckooCriticalError(f"Invalid QEMU guest {machine_id}: {error}") from error
            if not path_exists(profile["cmdline"][0]):
                raise CuckooCriticalError(f"QEMU binary not found for {machine_id}: {profile['cmdline'][0]}")
            for key in ("firmware", "firmware_vars", "seed_image"):
                filepath = paths[key]
                if not filepath:
                    continue
                if not path_exists(filepath):
                    raise CuckooCriticalError(f"Required guest file not found for {machine_id}: {filepath}")
            if paths["firmware_vars"] and os.path.realpath(paths["firmware_vars"]) == os.path.realpath(
                paths["firmware_vars_runtime"]
            ):
                raise CuckooCriticalError(f"Firmware runtime file must differ from its golden copy for {machine_id}")
            params = dict(cape_qemu.QEMU_ARGS["default"]["params"])
            params.update(profile["params"])
            params.update({"imagepath": os.path.dirname(image), "vmname": machine_id})
            for key in ("kernel", "initrd"):
                if f"-{key}" in profile["cmdline"]:
                    filepath = str(machine.get(key) or params.get(key) or "").format(**params)
                    if not filepath or not path_exists(filepath):
                        raise CuckooCriticalError(f"Required {key} not found for {machine_id}: {filepath}")

    def _extra_qemu_args(self, machine, cmdline):
        task_ids = (
            self.db.session.execute(
                select(Task.id).where(
                    Task.machine_id == machine.id,
                    Task.status == TASK_RUNNING,
                )
            )
            .scalars()
            .all()
        )

        if len(task_ids) != 1:
            raise CuckooMachineError(f"Expected one running task for {machine.label}, found {len(task_ids)}")

        pcap_path = os.path.join(CUCKOO_ROOT, "storage", "analyses", str(task_ids[0]), "dump.pcap")

        if not os.path.isdir(os.path.dirname(pcap_path)):
            raise CuckooMachineError(f"Analysis directory missing: {pcap_path}")
        if os.path.lexists(pcap_path):
            raise CuckooMachineError(f"PCAP already exists: {pcap_path}")

        options = getattr(self.options, machine.name)
        network_model = options.get("analysis_network_model") or self._network_device(cmdline)
        network_args, capture_netdev = _mace_network_args(options, network_model)
        netdevs = []
        for index, argument in enumerate(cmdline[:-1]):
            if argument == "-netdev":
                match = re.search(r"(?:^|,)id=([^,]+)", cmdline[index + 1])
                if match:
                    netdevs.append(match.group(1))
        if capture_netdev:
            if capture_netdev in netdevs:
                raise CuckooMachineError(f"Duplicate QEMU analysis netdev: {capture_netdev}")
        else:
            capture_netdev = options.get("capture_netdev") or (netdevs[0] if netdevs else None)
            if capture_netdev not in netdevs:
                raise CuckooMachineError(f"Capture netdev does not exist for {machine.name}: {capture_netdev}")
        return network_args + [
            "-object",
            f"filter-dump,id=cape_pcap,netdev={capture_netdev},file={pcap_path}",
        ]

    def start(self, label):
        machine = self.db.view_machine_by_label(label)
        machine_options = getattr(self.options, machine.name)
        paths = self._guest_paths(machine_options, machine.name)
        agent_url = f"http://{machine.ip}:8000/"

        # Hold the controller lock through QEMU's TAP attachment, then release
        # it before waiting for the agent. down detects the attached TAP fd.
        with _mace_lab_lock(machine_options):
            if paths["firmware_vars"]:
                shutil.copyfile(paths["firmware_vars"], paths["firmware_vars_runtime"])
                os.chmod(paths["firmware_vars_runtime"], 0o600)

            if paths["console_log"] and os.path.exists(paths["console_log"]):
                os.unlink(paths["console_log"])

            super().start(label)
            _mace_wait_tap(machine_options, self.state[machine.name])

        started_at = time.monotonic()
        agent_timeout = int(machine_options.get("agent_timeout") or Config().timeouts.critical)
        deadline = started_at + agent_timeout
        last_error = "no response"

        log.info(
            "Waiting for CAPE Agent at %s for up to %d seconds",
            agent_url,
            agent_timeout,
        )

        with requests.Session() as session:
            session.trust_env = False
            session.proxies = {}

            while time.monotonic() < deadline:
                if self.state[machine.name].poll() is not None:
                    raise CuckooMachineError(f"QEMU exited before the CAPE Agent became ready for {label}")
                try:
                    response = session.get(agent_url, timeout=2)
                    payload = response.json()

                    if response.status_code == 200 and isinstance(payload, dict) and payload.get("version"):
                        log.info(
                            "CAPE Agent ready for %s after %d seconds (version=%s)",
                            label,
                            int(time.monotonic() - started_at),
                            payload["version"],
                        )
                        return

                    last_error = f"HTTP {response.status_code}: {payload}"
                except (requests.RequestException, ValueError) as exc:
                    last_error = str(exc)

                time.sleep(2)

        try:
            self.stop(label)
        except Exception:
            log.exception(
                "Unable to stop %s after CAPE Agent readiness timeout",
                label,
            )

        raise CuckooMachineError(f"CAPE Agent did not become ready at {agent_url}: {last_error}")
