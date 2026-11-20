# The analyzer inside the guest

The host transfers the analyzer directory for the selected platform. The analyzer reads the task options and coordinates the package and auxiliary modules throughout the session. [Windows entry point](windows/analyzer.py) · [Linux entry point](linux/analyzer.py)

The **package** determines how to open the target. Launching an executable and opening a document in its associated application require different steps. [Windows packages](windows/modules/packages) · [Linux packages](linux/modules/packages)

On Windows, the monitor can record process activity and API calls. The guest transfers logs and captured files to the host. During processing, CAPE can identify a dump as a payload or extract configuration data from it.

On Linux, the Tracee auxiliary module collects events when enabled and available. It uploads its log as `logs/tracee.log` and can upload captured files under `tracee/` using names derived from their digests. The host parser reads the log from the analysis directory and produces the `tracee` section. To trace an event through the pipeline, compare its guest log entry with the parser output. [Guest collector](linux/modules/auxiliary/tracee.py) · [Host parser](../modules/processing/tracee.py)

## Module catalogs

- [Linux guest auxiliary](linux/modules/auxiliary/LINUX_AUXILIARIES.md)
- [Linux guest packages](linux/modules/packages/LINUX_ANALYSIS_PACKAGES.md)
- [Windows guest auxiliary](windows/modules/auxiliary/WINDOWS_AUXILIARIES.md)
- [Windows guest packages](windows/modules/packages/WINDOWS_ANALYSIS_PACKAGES.md)

## Package interface inside the guest

On Windows, the analyzer passes the target to `Package.start(target)`. A package can return process IDs for monitoring. During execution the analyzer calls `check()`, and `finish()` gives the package a chance to collect final data. The concrete package chooses the application that opens the target. [Windows package base](windows/lib/common/abstracts.py) · [Windows analyzer](windows/analyzer.py)

Many Linux packages specialize `prepare()` on the package class in `lib/core/packages.py`. For example, the Bash package makes the submitted script an argument to Bash, then relies on the base class to launch it. Follow the import in the package file to find the base implementation used by that package. [Linux package base](linux/lib/core/packages.py) · [Bash package](linux/modules/packages/bash.py) · [Linux analyzer](linux/analyzer.py)
