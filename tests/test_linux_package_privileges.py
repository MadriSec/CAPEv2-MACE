import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


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


if __name__ == "__main__":
    unittest.main()
