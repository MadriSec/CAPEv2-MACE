# The control service inside the guest

The agent is the service the host contacts once the guest operating system is ready. This directory contains implementations in two languages. [Python agent](agent.py) · [Go agent](go/README.md)

To follow a request, start at `GuestManager.start_analysis()` on the host. The host waits for the agent to respond, reads its information, prepares a working directory, and sends the analyzer archive and task configuration. For a file task, it also transfers the target. It then asks the agent to start the analyzer and polls the guest for status updates. [Host-side caller](../lib/cuckoo/core/guest.py)

A machine can be running while its agent is still starting. An agent response confirms the control channel is available. To determine whether the target started, follow the analyzer package. To verify delivery of the collected data, inspect the task directory on the host. [Analyzer packages](../analyzer/GUEST_ANALYZERS.md)

## Host-to-guest control interface

GuestManager acts as the HTTP client and the guest agent serves the requests. The sequence below describes a dynamic file task. [Client implementation](../lib/cuckoo/core/guest.py) · [Python handlers](agent.py)

| Request | What crosses the boundary | How the host uses it |
| --- | --- | --- |
| `GET /` and `GET /environ` | Agent information, supported features, and guest environment | Choose a compatible launch method and guest paths. |
| `POST /extract` | Analyzer ZIP and destination directory | Install the analyzer files for this task. |
| `POST /store` | File content and a guest destination path | Deliver the generated `analysis.conf`, the sample, and any task scripts. |
| `POST /execpy` or `POST /execute` | Analyzer launch request | Start the analyzer using the agent's supported interface. |
| `GET /status` | Guest-side execution status | Track the running session. The scheduler and processor maintain the separate task status exposed by the web API. |

Captured files and monitor logs travel back to the host through the [ResultServer interface](../lib/HOST_TASK_LIFECYCLE.md).
