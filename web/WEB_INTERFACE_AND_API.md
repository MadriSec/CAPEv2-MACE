# Following a task through the Django interface

1. The submission views receive the target and options from the web form. Registration produces the task IDs used to track the analysis. The scheduler subsequently selects a machine. [Submission views](submission/views.py) · [Scheduler](../lib/cuckoo/core/scheduler.py)
2. The API views expose submission and lookup operations to automated clients. Each task ID identifies a specific analysis, including when the same file has been submitted several times. [API views](apiv2/views.py)
3. The analysis views retrieve the results for the report pages. The sections available to the reader depend on what the processing and reporting stages produced. [Analysis views](analysis/views.py)

To identify the source of a displayed payload, trace it from the page to `CAPE.payloads`, then to the module that populated that field, and finally to the captured file in the task directory. The same path helps locate where an expected report section first became empty. [CAPE processor](../modules/processing/CAPE.py)

## HTTP API used by clients

These routes are mounted under `/apiv2/`. The views check the endpoint configuration and the caller's access to the task. [Django URL configuration](web/urls.py) · [API routes](apiv2/urls.py) · [Request handlers](apiv2/views.py)

| Request | Input | Successful response |
| --- | --- | --- |
| `POST /apiv2/tasks/create/file/` | Multipart upload in the `file` field and optional task settings | The new IDs in `data.task_ids`. Follow each ID separately. |
| `GET /apiv2/tasks/status/<id>/` | Task ID in the path | The current task status in `data`, for example `completed` or `reported`. |
| `GET /apiv2/tasks/view/<id>/` | Task ID in the path | Task details, including the recorded state. |

The browser form follows its own Django view. For a problem accepting an upload, start with the view for the entry point the user chose. For a task that already has an ID but stays pending, follow the scheduler. [Browser submission](submission/views.py) · [Scheduler](../lib/cuckoo/core/scheduler.py)
