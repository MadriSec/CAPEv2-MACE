#!/usr/bin/env python
# Copyright (C) 2018 phdphuc
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.

from os import chmod, stat
from shlex import quote

from lib.core.packages import Package


class Generic(Package):
    """Generic analysis package."""

    def prepare(self):
        chmod(self.target, stat(self.target).st_mode | 0o111)
        self.target = quote(self.target)
