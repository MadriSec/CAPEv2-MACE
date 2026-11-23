#!/usr/bin/env python
# Copyright (C) 2015 Dmitry Rodionov
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.

import inspect
import importlib
import logging
import pwd
import shlex
import shutil
import subprocess
import timeit
from os import environ, makedirs, path, sys
from threading import Event, Thread

from lib.common.constants import OPT_CURDIR
from lib.common.results import NetlogFile, append_buffer_to_host

log = logging.getLogger(__name__)


def choose_package_class(file_type=None, file_name="", suggestion=None):
    if suggestion is not None:
        name = suggestion
    else:
        name = _guess_package_name(file_type, file_name)
        if not name:
            log.info("_guess_package_name failed")
            log.info(file_type)
            log.info(file_name)
            name = "generic"

    full_name = f"modules.packages.{name}"
    try:
        # FIXME(rodionovd):
        # I couldn't figure out how to make __import__ import anything from
        # the (grand)parent package, so here I just patch the PATH
        sys.path.append(path.abspath(path.join(path.dirname(__file__), "..", "..")))
        # Since we don't know the package class yet, we'll just import everything
        # from this module and then try to figure out the required member class
        module = importlib.import_module(full_name)
    except ImportError:
        raise Exception(f'Unable to import package "{name}": it does not exist')
    try:
        pkg_class = _found_target_class(module, name)
    except IndexError as err:
        raise Exception(f"Unable to select package class (package={full_name}): {err}")
    return pkg_class


def _found_target_class(module, name):
    """Searches for a class with the specific name: it should be
    equal to capitalized $name.
    """
    for member in inspect.getmembers(module, inspect.isclass):
        if member[0] == name.capitalize():
            return member[1]


def _guess_package_name(file_type, file_name):
    try:
        if "Bourne-Again" in file_type or "bash" in file_type or file_name.endswith(".sh"):
            return "bash"
        elif "POSIX tar archive" in file_type or file_name.endswith("tar"):
            return "archive"
        elif "Zip archive" in file_type or file_name.endswith(".zip"):
            return "zip"
        elif "7-zip archive data" in file_type or file_name.endswith(".7z"):
            return "archive"
        elif "RAR archive data" in file_type or file_name.endswith(".rar"):
            return "archive"
        elif "ISO 9660 CD-ROM filesystem data" in file_type or file_name.endswith(".iso"):
            return "archive"
        elif "gzip compressed data" in file_type or file_name.endswith((".tgz", ".gz")):
            return "zip"
        elif "bzip2 compressed data" in file_type or file_name.endswith((".tbz", ".tbz2")):
            return "zip"
        elif "PDF document" in file_type or file_name.endswith(".pdf"):
            return "pdf"
        elif "Composite Document File V2 Document" in file_type or file_name.endswith(".doc"):
            return "doc"
        elif "Microsoft Word" in file_type or file_name.endswith(".docx"):
            return "doc"
        elif "ELF" in file_type:
            return "generic"
        elif "Debian binary package" in file_type or file_name.endswith(".deb"):
            return "deb"
        elif "Perl script text executable" in file_type or file_name.endswith(".pl"):
            return "perl"
        elif "Python script" in file_type or file_name.endswith(".py"):
            return "python"
        elif "a pwsh script" in file_type or file_name.endswith(".ps1"):
            return "ps1"
        elif file_name.endswith(".whl"):
            return "python_whl"
        elif "Unicode text" in file_type or file_name.endswith(".js"):
            return "js"
    except (TypeError, AttributeError):
        pass
    return None


def create_custom_folders(directory_path: str):
    """Create custom folders (recursively) given the full path."""
    if path.exists(directory_path):
        log.info("%s already exists, skipping creation", directory_path)
    else:
        try:
            makedirs(directory_path)
            log.info("%s created", directory_path)
        except OSError:
            log.error("Unable to create user-defined custom folder directory")


SAMPLE_USER = "cape-sample"


def get_sample_account():
    try:
        account = pwd.getpwnam(SAMPLE_USER)
    except KeyError:
        subprocess.run(
            ["sudo", "-n", "/usr/sbin/useradd", "--system", "--user-group",
             "--create-home", "--shell", "/usr/sbin/nologin", SAMPLE_USER],
            check=True,
            timeout=30,
        )
        account = pwd.getpwnam(SAMPLE_USER)

    if account.pw_uid == 0 or account.pw_gid == 0:
        raise ValueError(f"{SAMPLE_USER} must have a non-root UID and GID")
    return account


def strace_command(target, options):
    run_as_root = _string_to_bool(options.get("run_as_root", False))
    trace_args = shlex.split(options.get("strace_args", "").replace(";", ","))
    command = ["sudo", "-n", "strace", "-o", "/dev/stderr", "-s", "800", *trace_args, "-ttf", "--"]
    if options.get("nohuman"):
        target = ["xterm", "-hold", "-e", *target]
    if run_as_root:
        log.info("Sample execution requested as root (UID 0)")
        return [*command, *target]

    # Injection and other tracer controls could alter the privilege drop itself.
    if len(trace_args) % 2 or any(
        flag != "-e" or not expression.startswith("trace=")
        for flag, expression in zip(trace_args[::2], trace_args[1::2])
    ):
        raise ValueError("Non-root analysis only supports strace_args filters of the form '-e trace=...'")

    account = get_sample_account()
    log.info("Sample execution requested as %s (UID %d)", SAMPLE_USER, account.pw_uid)
    return [
        *command,
        "/usr/bin/setpriv",
        f"--reuid={account.pw_uid}",
        f"--regid={account.pw_gid}",
        "--clear-groups",
        "--no-new-privs",
        "--reset-env",
        "--",
        *target,
    ]


class Package:
    """Base analysis package"""

    def __init__(self, target, **kwargs):
        if not target:
            raise Exception("Package(): 'target' and 'host' arguments are required")

        self.target = target
        # Any analysis options?
        self.options = kwargs.get("options", {})
        # A timeout for analysis
        self.timeout = kwargs.get("timeout")
        # Command-line arguments for the target.

        def _args():
            args = self.options.get("arguments")
            if isinstance(args, list):
                return args
            if isinstance(args, str):
                return args.split()
            return []

        self.args = _args()

        # Choose an analysis method (or fallback to apicalls)
        self.method = self.options.get("method", "apicalls")
        # Should our target be launched as root or not
        self.run_as_root = _string_to_bool(self.options.get("run_as_root", "False"))
        # free: do not inject our monitor.
        self.free = self.options.get("free")
        self.proc = None
        self.pids = []
        self.strace_output = kwargs.get("strace_output", "/tmp")
        self.nc = NetlogFile()
        self.thread = None
        self._read_ready_ev = Event()

    def set_pids(self, pids):
        """Update list of monitored PIDs in the package context.
        @param pids: list of pids.
        """
        self.pids = pids

    def prepare(self):
        """Preparation routine. Do anything you want here."""
        pass

    def move_curdir(self, filepath):
        """Move a file to the current working directory so it can be executed
        from there.
        @param filepath: the file to be moved
        @return: the new filepath
        """
        if OPT_CURDIR not in self.options:
            return filepath

        curdir = path.expandvars(self.options[OPT_CURDIR])
        create_custom_folders(curdir)

        if not path.exists(curdir):
            return filepath

        newpath = path.join(curdir, path.basename(filepath))
        shutil.move(filepath, newpath)
        return newpath

    def start(self):
        """Runs an analysis process.
        This function is a generator.
        """
        target_name = self.options.get("filename")
        if target_name:
            filepath = path.join(environ.get("TEMP", "/tmp"), target_name)
            # Remove the trailing slash (if any)
            self.target = filepath.rstrip("/")
        self.target = self.move_curdir(self.target)
        self.prepare()
        self.nc.init("logs/strace.log", False)
        self.thread = Thread(target=self.thread_send_strace_buffer, daemon=True)
        self.thread.start()
        self.strace_analysis()

        return self.proc.pid

    def check(self):
        """Check."""
        return True

    def package_files(self):
        """A list of files to upload to host.
        The list should be a list of tuples (<path on guest>, <name of file in package_files folder>).
        (package_files is a folder that will be created in analysis folder).
        """
        return None

    def thread_send_strace_buffer(self):
        # wait for the subprocess to start
        self._read_ready_ev.wait()
        for line in self.proc.stderr:
            try:
                append_buffer_to_host(line, self.nc)
            except ConnectionResetError:
                log.info("Strace streaming connection has been closed")
                return
            except Exception as e:
                log.exception("Exception occured: %s", e)

    def finish(self):
        """Finish run.
        If specified to do so, this method dumps the memory of
        all running processes.
        """
        self.nc.close()
        return True

    def get_pids(self):
        return []

    def strace_analysis(self):
        target = [*shlex.split(self.target), *self.args]
        cmd = strace_command(target, self.options)
        log.info("Executing with strace: %s", shlex.join(cmd))
        self.proc = subprocess.Popen(
            cmd, env={"XAUTHORITY": "/root/.Xauthority", "DISPLAY": ":0"}, stderr=subprocess.PIPE
        )
        self._read_ready_ev.set()
        log.info("Process started with strace")
        return True

    def normal_analysis(self):
        kwargs = {"args": self.args, "timeout": self.timeout, "run_as_root": self.run_as_root}

        # cmd = apicalls(self.target, **kwargs)
        cmd = f"{self.target} {' '.join(kwargs['args'])}"
        process_start = timeit.default_timer()
        self.proc = subprocess.Popen(
            cmd, env={"XAUTHORITY": "/root/.Xauthority", "DISPLAY": ":0"}, stderr=subprocess.PIPE, shell=True
        )

        log.debug(self.proc.stderr.readline())

        process_stop = timeit.default_timer()
        log.info("Process startup took %.2f seconds", process_start - process_stop)
        return True

    @staticmethod
    def _upload_file(local, remote):
        if path.exists(local):
            nf = NetlogFile(remote)
            with open(local, "rb") as f:
                for chunk in f:
                    nf.sock.sendall(chunk)  # dirty direct send, no reconnecting
            nf.close()


def _string_to_bool(raw):
    if isinstance(raw, bool):
        return raw
    if not isinstance(raw, str):
        raise ValueError("run_as_root must be a boolean")
    return raw.lower() in ("yes", "true", "t", "1")
