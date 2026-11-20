# How CAPE builds a report

The plugins in this directory run on the host. The plugin registry connects each group to a stage in the analysis lifecycle. [Plugin registry and runners](../lib/cuckoo/core/plugins.py)

| Group | Responsibility |
| --- | --- |
| [machinery](machinery) | Translates machine management requests into operations for the selected backend, such as KVM or QEMU. |
| [auxiliary](auxiliary) | Provides services such as network capture during dynamic analysis. |
| [processing](processing) | Reads artifacts and metadata and populates sections of the shared results dictionary. |
| [signatures](signatures) | Looks for behavioral patterns in processed data and records matches. |
| [reporting](reporting) | Serializes, stores, or forwards results to the configured destinations. |

For network activity, follow the network processor. It can turn a packet capture in `dump.pcap` into network conversations and decoded requests. [Network processor](processing/network.py)

For an extracted payload, follow the CAPE processor. It examines captured files, uses file identification data and available extractors, and records results under `CAPE.payloads` and `CAPE.configs`. It links configurations to file hashes so an analyst can trace a value back to the source artifact. [CAPE processor](processing/CAPE.py)

The JSON reporter is one consumer of these results. Extracting a configuration requires both observable data and a parser that recognizes it. An empty configuration list can reflect a gap in either collection or parsing. [JSON reporter](reporting/jsondump.py)

## Module catalogs

- [Auxiliary](auxiliary/HOST_AUXILIARIES.md)
- [Feeds](feeds/FEED_PLUGINS.md)
- [Machinery](machinery/MACHINERY_BACKENDS.md)
- [Processing](processing/ARTIFACT_PROCESSING.md)
- [Reporting](reporting/REPORTING_MODULES.md)
- [Signatures](signatures/BEHAVIORAL_SIGNATURES.md)

## Python interfaces used by the host

The base classes define the extension points. The runner shows which values a plugin actually receives and what happens to its output. [Base classes](../lib/cuckoo/common/abstracts.py) · [Plugin runners](../lib/cuckoo/core/plugins.py)

| Interface | Who calls it | Inputs and observable result |
| --- | --- | --- |
| `Machinery.start(label)` and `stop(label)` | Host machinery management | The backend receives a machine label and changes that machine's lifecycle state. |
| `Auxiliary.start()` and `stop()` | Auxiliary runner around the guest session | The module receives task, machine, and options before startup. A collector can write an artifact during the session. |
| `Processing.run()` | `RunProcessing` | The runner supplies the task, analysis directory, and module options. It takes the return value and places it under the module's `key` in the shared results. |
| `Signature.on_call(call, process)`, `on_complete()`, or `run()` | `RunSignatures` | Evented signatures can examine individual calls and finish evaluation at the end. Other signatures evaluate the assembled results. Matches provide evidence for the report. |
| `Report.run(results)` | `RunReporting` | A reporter receives the shared results and can write a file, update a backend, or pass the data to a configured destination. |

For example, the Tracee processor reads the guest log and sets its key to `tracee`. A reporter can then read that section from the shared dictionary. [Tracee processor](processing/tracee.py) · [JSON reporter](reporting/jsondump.py)
