# The task lifecycle on the host

The operational database tracks tasks, states, and machine assignments. CAPE stores artifacts on the filesystem by task ID. A reporting backend can also store processed results for later retrieval.

1. The scheduler looks for a task it can service. Some tasks run entirely on the host, while others require a compatible analysis machine. The scheduler hands the task to an AnalysisManager thread. [Scheduler](cuckoo/core/scheduler.py)
2. In `AnalysisManager.perform_analysis()`, the manager prepares storage and checks the task category. For dynamic analysis it enters the contexts that manage the machine, ResultServer registration, routing, and auxiliary modules. These contexts close in reverse order when the session ends. [AnalysisManager](cuckoo/core/analysis_manager.py)
3. GuestManager opens the control channel to the agent, sends the analyzer, options, and target, and tracks guest status. The ResultServer receives data flowing back from the guest. Registering the machine for the task lets it associate incoming logs and files with the correct analysis directory. [GuestManager](cuckoo/core/guest.py) · [ResultServer](cuckoo/core/resultserver.py)

## Interpreting task status

In `launch_analysis()`, an unusable machine can send a task back to `pending` for reassignment. An unexpected exception sets `failed_analysis`. If `perform_analysis()` returns normally, even if it returns false, the manager sets `completed` and logs the outcome. Check the task log and artifacts to assess what CAPE collected. The processor updates the reporting status separately. [Processor](../utils/SUBMISSION_AND_PROCESSING.md)

## Host files and the interfaces they own

| File | Caller and responsibility |
| --- | --- |
| [startup.py](cuckoo/core/startup.py) | The host entry point calls its startup checks and initialization functions before scheduling tasks. |
| [database.py](cuckoo/core/database.py) | Supplies the operational database interface used to look up tasks, record status, and coordinate machine assignment. |
| [machinery_manager.py](cuckoo/core/machinery_manager.py) | Connects scheduler and analysis lifecycle operations to the selected machinery implementation. |
| [rooter.py](cuckoo/core/rooter.py) | Sends networking requests from the host application to the privileged [rooter service](../utils/rooter.py). |
| [plugins.py](cuckoo/core/plugins.py) | Discovers plugin classes and runs them with the task, options, and analysis data appropriate to each stage. |
| [resultserver.py](cuckoo/core/resultserver.py) | Receives guest evidence. Its command map dispatches incoming streams to the corresponding storage handler. |

### Guest-to-host evidence interface

AnalysisManager registers the task and machine before the guest sends evidence. The ResultServer dispatches `FILE` uploads to the file handler, `LOG` streams to the text log handler, and `BSON` or `PROTO` streams to their respective binary handlers. The registered task determines which analysis directory receives the data. For a missing artifact, trace its guest producer, the matching handler, and the file expected by the processor. [Task registration](cuckoo/core/analysis_manager.py) · [Protocol handlers](cuckoo/core/resultserver.py)
