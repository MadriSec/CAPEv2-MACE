import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


class LinuxPackagePrivileges(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "analyzer/linux/lib/core/packages.py"
        spec = importlib.util.spec_from_file_location("linux_guest_packages", path)
        self.module = importlib.util.module_from_spec(spec)
        guest_modules = {
            "lib.common.constants": SimpleNamespace(OPT_CURDIR="curdir"),
            "lib.common.results": SimpleNamespace(NetlogFile=object, append_buffer_to_host=None),
        }
        with patch.dict(sys.modules, guest_modules):
            spec.loader.exec_module(self.module)

    def test_default_drops_privileges_before_exec(self):
        with patch.object(self.module, "get_sample_account", return_value=SimpleNamespace(pw_uid=995, pw_gid=995)):
            command = self.module.strace_command(["/tmp/sample name", "literal; argument"], {})
        target = command[command.index("--") + 1 :]
        self.assertEqual(command[:3], ["sudo", "-n", "strace"])
        self.assertEqual(target[:3], ["/usr/bin/setpriv", "--reuid=995", "--regid=995"])
        self.assertIn("--clear-groups", target)
        self.assertIn("--no-new-privs", target)
        self.assertEqual(target[-2:], ["/tmp/sample name", "literal; argument"])

    def test_root_requires_explicit_true(self):
        with patch.object(self.module, "get_sample_account") as account:
            command = self.module.strace_command(["/tmp/benign"], {"run_as_root": "true"})
        account.assert_not_called()
        self.assertEqual(command[command.index("--") + 1 :], ["/tmp/benign"])

    def test_nonroot_allows_filters_but_rejects_launcher_options(self):
        with patch.object(self.module, "get_sample_account", return_value=SimpleNamespace(pw_uid=995, pw_gid=995)):
            command = self.module.strace_command(["/tmp/benign"], {"strace_args": "-e trace=read;write"})
            self.assertIn("trace=read,write", command)
            with self.assertRaises(ValueError):
                self.module.strace_command(["/tmp/benign"], {"strace_args": "-u root"})


    def test_sample_account_is_prepared_explicitly(self):
        account = SimpleNamespace(pw_uid=995, pw_gid=995)
        with (
            patch.object(self.module.pwd, "getpwnam", side_effect=[KeyError, KeyError, account]),
            patch.object(self.module.subprocess, "run") as run,
        ):
            with self.assertRaises(KeyError):
                self.module.get_sample_account()
            run.assert_not_called()
            self.module.prepare_sample_account({"run_as_root": "false"})
            self.assertEqual(run.call_args.args[0][2], "/usr/sbin/useradd")

        with patch.object(self.module.pwd, "getpwnam") as lookup:
            self.module.prepare_sample_account({"run_as_root": "true"})
        lookup.assert_not_called()

    def test_tracer_choice_respects_profile(self):
        self.assertEqual(self.module.select_tracer({}, True), "both")
        self.assertEqual(self.module.select_tracer({}, False), "strace")
        self.assertEqual(self.module.select_tracer({"tracer": "strace"}, True), "strace")
        for tracer in ("tracee", "both", "invalid"):
            with self.assertRaises(ValueError):
                self.module.select_tracer({"tracer": tracer}, False)

    def test_launches_only_requested_tracers(self):
        for tracer in ("strace", "tracee", "both"):
            with self.subTest(tracer=tracer), tempfile.TemporaryDirectory() as directory:
                shim = Path(directory) / "cape-sample-run"
                shim.touch()
                options = {"tracer": tracer, "run_as_root": False}
                with (
                    patch.object(self.module, "SAMPLE_LAUNCHER", shim),
                    patch.object(self.module, "get_sample_account", return_value=SimpleNamespace(pw_uid=995, pw_gid=995)),
                    patch.object(self.module.subprocess, "Popen") as popen,
                ):
                    connection = MagicMock()
                    self.module.launch_sample(["/tmp/benign"], options, connection)
                argv = popen.call_args.args[0]
                self.assertEqual("strace" in argv, tracer != "tracee")
                self.assertEqual(str(shim) in argv, tracer != "strace")
                self.assertEqual(connection.init.called, tracer != "tracee")
                self.assertEqual(argv[-1], "/tmp/benign")
                self.assertIn("--reuid=995", argv)
                if tracer != "strace":
                    self.assertLess(argv.index(str(shim)), argv.index("--reuid=995"))


if __name__ == "__main__":
    unittest.main()
