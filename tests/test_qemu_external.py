"""Guest selection and boot regression tests, without starting a real VM."""

import copy
import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from lib.cuckoo.common.dictionary import Dictionary
from lib.cuckoo.common.exceptions import CuckooCriticalError, CuckooMachineError

# Interface enumeration is unrelated to command construction and may be
# unavailable in a sandbox or CI container.
with patch("psutil.net_if_addrs", return_value={}):
    from modules.machinery import qemu, qemu_external


class TestQEMUExternal(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        for profile in qemu.QEMU_ARGS.values():
            (self.bin_dir / Path(profile["cmdline"][0]).name).touch()
        (self.bin_dir / "qemu-img").touch()
        (self.root / "storage" / "analyses" / "101").mkdir(parents=True)

    def guest_options(self, arch="x64", **overrides):
        image_dir = self.root / "guests" / (arch or "default")
        image_dir.mkdir(parents=True, exist_ok=True)
        image = image_dir / "golden.qcow2"
        image.touch()
        options = Dictionary(
            arch=arch,
            image=str(image),
            snapshot="",
            memory="2G",
            cpu="",
            enable_kvm=False,
            label="guest",
            ip="127.0.0.1",
            platform="linux",
            mac="52:54:00:12:34:56",
        )
        options.update(overrides)
        return options

    def firmware_options(self, arch="arm64", **overrides):
        options = self.guest_options(arch)
        image_dir = Path(options.image).parent
        for name in ("code.fd", "vars.golden.fd", "seed.img"):
            (image_dir / name).write_bytes(b"golden")
        options.update(
            firmware="{imagepath}/code.fd",
            firmware_vars="{imagepath}/vars.golden.fd",
            seed_image="{imagepath}/seed.img",
            network="user",
        )
        options.update(overrides)
        return options

    def backend(self, **guests):
        backend = object.__new__(qemu_external.QEMUExternal)
        backend.options = Dictionary(
            qemu_external=Dictionary(path=str(self.bin_dir / "qemu-system-x86_64"), machines=list(guests)),
            **guests,
        )
        backend.qemu_dir = str(self.bin_dir)
        backend.qemu_img = str(self.bin_dir / "qemu-img")
        backend.state = {}
        backend.db = MagicMock()
        backend.db.session.execute.return_value.scalars.return_value.all.return_value = [101]
        backend.db.view_machine_by_label.side_effect = lambda label: self.machine(label, guests[label])
        return backend

    @staticmethod
    def machine(name, options):
        return SimpleNamespace(id=1, name=name, label=name, ip=options.ip)

    def launch(self, backend, name):
        overlay = MagicMock()
        overlay.communicate.return_value = ("", "")
        process = MagicMock()
        process.poll.return_value = None
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = {"version": "test"}
        with (
            patch.object(qemu.subprocess, "Popen", side_effect=[overlay, process]) as popen,
            patch.object(qemu_external.requests, "Session", return_value=session),
            patch.object(qemu_external, "CUCKOO_ROOT", str(self.root)),
        ):
            backend.start(name)
        return popen.call_args_list[-1].args[0]

    def test_import_does_not_replace_shared_architecture_profiles(self):
        profiles = copy.deepcopy(qemu.QEMU_ARGS)
        importlib.reload(qemu_external)
        self.assertEqual(qemu.QEMU_ARGS, profiles)

    def test_all_existing_architectures_select_their_own_executable(self):
        profiles = copy.deepcopy(qemu.QEMU_ARGS)
        for arch, profile in profiles.items():
            if arch == "default":
                continue
            with self.subTest(arch=arch):
                options = self.guest_options(arch)
                backend = self.backend(guest=options)
                command = backend._get_qemu_args(options)["cmdline"]
                self.assertEqual(command[0], str(self.bin_dir / profile["cmdline"][0]))
                self.assertIn("-monitor", command)
                self.assertFalse(any("pflash" in argument for argument in command))
        self.assertEqual(qemu.QEMU_ARGS, profiles)

    def test_unspecified_architecture_uses_x64(self):
        for arch in (None, "", "default"):
            with self.subTest(arch=arch):
                options = self.guest_options(arch)
                backend = self.backend(guest=options)
                backend._initialize_check()
                command = self.launch(backend, "guest")
                self.assertEqual(Path(command[0]).name, "qemu-system-x86_64")
                self.assertIn(str(Path(options.image).parent / "snapshot_guest.qcow2"), command)
                self.assertFalse(any("AAVMF" in argument for argument in command))

    def test_x86_guests_start_without_arm_files_or_firmware_copy(self):
        for arch, binary in (("x64", "qemu-system-x86_64"), ("x86", "qemu-system-i386")):
            with self.subTest(arch=arch):
                options = self.guest_options(arch)
                backend = self.backend(guest=options)
                backend._initialize_check()
                with patch.object(qemu_external.shutil, "copyfile") as copyfile:
                    command = self.launch(backend, "guest")
                copyfile.assert_not_called()
                self.assertEqual(Path(command[0]).name, binary)
                self.assertIn("netdev=net_guest", command[-1])
                self.assertFalse(any("pflash" in argument or "seed" in argument for argument in command))

    def test_kernel_boot_arm_guests_do_not_require_uefi(self):
        for arch, binary in (("arm", "qemu-system-arm"), ("arm64", "qemu-system-aarch64")):
            with self.subTest(arch=arch):
                options = self.guest_options(arch)
                image_dir = Path(options.image).parent
                for name in ("kernel", "initrd"):
                    (image_dir / name).touch()
                    options[name] = "{imagepath}/" + name
                backend = self.backend(guest=options)
                backend._initialize_check()
                command = self.launch(backend, "guest")
                self.assertEqual(Path(command[0]).name, binary)
                self.assertIn(str(image_dir / "kernel"), command)
                self.assertIn(str(image_dir / "initrd"), command)
                self.assertFalse(any("pflash" in argument for argument in command))

    def test_mixed_x64_and_arm64_guests_keep_separate_boot_settings(self):
        x64 = self.guest_options("x64")
        arm64 = self.firmware_options(qemu_machine="virt,gic-version=3", smp=4, accel="tcg,thread=multi")
        backend = self.backend(intel=x64, arm=arm64)
        backend._initialize_check()
        intel_command = self.launch(backend, "intel")
        arm_command = self.launch(backend, "arm")
        self.assertEqual(Path(intel_command[0]).name, "qemu-system-x86_64")
        self.assertFalse(any("pflash" in argument for argument in intel_command))
        self.assertNotIn("-smp", intel_command)
        self.assertEqual(Path(arm_command[0]).name, "qemu-system-aarch64")
        self.assertIn("virt,gic-version=3", arm_command)
        self.assertIn("4", arm_command)
        self.assertIn("tcg,thread=multi", arm_command)
        self.assertNotIn("-kernel", arm_command)
        self.assertIn("netdev=net0", arm_command[-1])
        runtime = Path(arm64.image).parent / "firmware_vars_arm.fd"
        self.assertEqual(runtime.read_bytes(), b"golden")
        self.assertEqual(runtime.stat().st_mode & 0o777, 0o600)
        runtime.write_bytes(b"changed")
        self.launch(backend, "arm")
        self.assertEqual(runtime.read_bytes(), b"golden")

    def test_x64_uefi_uses_its_configured_firmware(self):
        options = self.firmware_options("x64")
        backend = self.backend(guest=options)
        backend._initialize_check()
        command = self.launch(backend, "guest")
        self.assertEqual(Path(command[0]).name, "qemu-system-x86_64")
        self.assertTrue(any("pflash" in argument for argument in command))
        self.assertFalse(any("AAVMF" in argument for argument in command))
        self.assertNotIn("-machine", command)

    def test_firmware_runtime_paths_are_unique_per_guest(self):
        options = self.firmware_options()
        first = qemu_external.QEMUExternal._guest_paths(options, "first")
        second = qemu_external.QEMUExternal._guest_paths(options, "second")
        self.assertNotEqual(first["firmware_vars_runtime"], second["firmware_vars_runtime"])
        options.firmware_vars_runtime = options.firmware_vars
        with self.assertRaisesRegex(CuckooCriticalError, "must differ"):
            self.backend(guest=options)._initialize_check()

    def test_only_configured_firmware_is_required(self):
        options = self.firmware_options()
        Path(options.image).parent.joinpath("code.fd").unlink()
        with self.assertRaisesRegex(CuckooCriticalError, "Required guest file"):
            self.backend(guest=options)._initialize_check()

    def test_missing_guest_binary_is_reported_for_that_architecture(self):
        options = self.guest_options("x86")
        (self.bin_dir / "qemu-system-i386").unlink()
        with self.assertRaisesRegex(CuckooCriticalError, "qemu-system-i386"):
            self.backend(guest=options)._initialize_check()

    def test_unknown_architecture_is_rejected(self):
        options = self.guest_options("unknown")
        with self.assertRaisesRegex(CuckooCriticalError, "Unsupported QEMU guest architecture"):
            self.backend(guest=options)._initialize_check()

    def test_missing_memory_uses_the_guest_profile_default(self):
        options = self.guest_options(memory=None)
        command = self.launch(self.backend(guest=options), "guest")
        self.assertEqual(command[command.index("-m") + 1], "1024M")

    def test_guest_can_override_its_qemu_executable(self):
        binary = self.bin_dir / "custom-qemu"
        binary.touch()
        options = self.guest_options(qemu_path=str(binary))
        backend = self.backend(guest=options)
        backend._initialize_check()
        self.assertEqual(self.launch(backend, "guest")[0], str(binary))

    def test_mace_capture_uses_the_guest_network_device_model(self):
        options = self.guest_options(
            "arm",
            analysis_tap="mace-arm",
            analysis_bridge="mace-br0",
            analysis_mac="52:54:00:12:34:57",
            analysis_lab_state="/tmp/lab.json",
        )
        backend = self.backend(guest=options)
        command = backend._get_qemu_args(options)["cmdline"]
        with patch.object(qemu_external, "CUCKOO_ROOT", str(self.root)):
            arguments = backend._extra_qemu_args(self.machine("guest", options), command)
        self.assertIn("virtio-net-device,netdev=net1,mac=52:54:00:12:34:57,romfile=", arguments)
        self.assertIn("netdev=net1", arguments[-1])

    def test_capture_rejects_a_netdev_absent_from_the_guest(self):
        options = self.guest_options(capture_netdev="net0")
        backend = self.backend(guest=options)
        with self.assertRaisesRegex(CuckooMachineError, "Capture netdev does not exist"):
            self.launch(backend, "guest")

    def test_user_network_relay_uses_configured_addresses_and_ports(self):
        options = self.guest_options(
            network="user",
            ip="127.0.0.2",
            ssh_port=2223,
            resultserver_relay=True,
            resultserver_ip="10.0.2.101",
            resultserver_port=2050,
            socat_path="/usr/bin/socat",
        )
        backend = self.backend(guest=options)
        config = SimpleNamespace(resultserver=SimpleNamespace(ip="127.0.0.3", port=2051))
        with patch.object(qemu_external, "Config", return_value=config):
            command = backend._get_qemu_args(options)["cmdline"]
        network = command[command.index("-netdev") + 1]
        self.assertIn("hostfwd=tcp:127.0.0.2:8000-:8000", network)
        self.assertIn("hostfwd=tcp:127.0.0.2:2223-:22", network)
        self.assertIn("guestfwd=tcp:10.0.2.101:2050-cmd:/usr/bin/socat STDIO TCP4:127.0.0.3:2051", network)

    def test_original_qemu_returns_independent_profiles(self):
        backend = object.__new__(qemu.QEMU)
        original = copy.deepcopy(qemu.QEMU_ARGS)
        options = self.guest_options("arm64")
        profile = backend._get_qemu_args(options)
        profile["cmdline"].append("changed")
        profile["params"]["memory"] = "changed"
        self.assertEqual(qemu.QEMU_ARGS, original)


if __name__ == "__main__":
    unittest.main()
