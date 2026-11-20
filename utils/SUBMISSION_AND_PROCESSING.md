# Submission and post-processing

The command-line submission utility registers analysis requests. Use the returned task ID to track the assignment in the database and find artifacts under `storage/analyses/<id>/`. [Submission utility](submit.py)

The processor works on collected data. In automatic mode, its task source normally selects tasks in the `completed` state. The processor initializes the results dictionary and runs `RunProcessing`, then `RunSignatures`, then `RunReporting` when reporting is requested. The `minproc` option skips signatures. After reporting, the error count determines whether the task becomes `reported` or `failed_reporting`. [Processor](process.py) · [Task source](../lib/cuckoo/core/processing_engine/source.py)

The scheduler and processor have separate service units. If artifacts already exist and the task is still `completed`, check the processor to see whether the task is waiting or being processed. Reprocessing lets an updated parser act on stored data. Observing an event that was never captured requires a new collection. [Scheduler service](../systemd/cape.service) · [Processor service](../systemd/cape-processor.service)
