# How CAPEv2 works

CAPE (*Config And Payload Extraction*) is a sandbox for malware analysis. A **sample** is the content being examined. Its SHA-256 hash identifies the file. A **task** is one analysis request, with its own ID, target, platform, and execution options. Two tasks can therefore share a sample hash and produce different observations.

## Following a file from submission to report

For a diagram of the application flow, including the static and PCAP branches, see the [application walkthrough](APPLICATION_FLOW.md).

1. **Submission.** The web interface, API, or CLI registers the request in the database and returns a task ID. The task enters the queue as `pending`. [Web interface and API](web/WEB_INTERFACE_AND_API.md) · [Command-line utilities](utils/SUBMISSION_AND_PROCESSING.md)
2. **Scheduling.** On the host, `cuckoo.py` initializes the database, plugins, routing, and ResultServer, then starts the scheduler. For dynamic analysis, the scheduler looks for a compatible machine. A task can remain in the queue while machines with different capabilities are idle. [Host entry point](cuckoo.py) · [Host components](lib/HOST_TASK_LIFECYCLE.md)
3. **Preparation.** AnalysisManager creates `storage/analyses/<id>/`, verifies the file hash, and stores the sample under `storage/binaries/<sha256>`. The `binary` entry in the task directory points to the sample. Tasks in the `static` and `pcap` categories proceed directly to processing on the host.
4. **Dynamic analysis.** The machinery backend manages the analysis machine. GuestManager contacts the agent inside the guest and transfers the analyzer, task options, and sample. The analyzer launches the target using a package for the selected platform. [Guest agent](agent/GUEST_AGENT.md) · [Analyzer](analyzer/GUEST_ANALYZERS.md)
5. **Collection.** The guest sends logs and files to the ResultServer on the host. The host can also collect artifacts such as a network capture. At the end of the session, AnalysisManager stops auxiliary modules, removes the task's routing rules, and releases the machine.
6. **Processing and reporting.** The processor reads the artifacts, builds structured results, runs signatures, and passes the results to reporting modules. Depending on what CAPE observed and which modules were enabled, the report can include process activity, network traffic, dropped files, payloads, and extracted configurations. [Modules](modules/HOST_PLUGINS.md) · [Configuration](conf/CONFIGURATION.md)

## Tracing a result back to its source

Suppose two Linux tasks analyze the same file but show different Tracee results. Use each task ID to locate its analysis directory and look for `logs/tracee.log`. If the log is missing, check collection inside the guest and transfer to the host. If it contains events, follow the host parser to see which events reach the `tracee` section. If the processed results contain that section but the web interface omits it, follow the reporting and display stages.
