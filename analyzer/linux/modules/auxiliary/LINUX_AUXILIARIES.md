# Linux guest auxiliary modules

The Linux analyzer runs these collectors and helpers alongside the selected analysis package.

| Source | Role |
| --- | --- |
| [filecollector.py](filecollector.py) | Watches filesystem events and collects files created or changed during the run. |
| [human.py](human.py) | Simulates user interaction inside the guest. |
| [screenshots.py](screenshots.py) | Captures screenshots of the guest display. |
| [tracee.py](tracee.py) | Collects Linux runtime events using Tracee and uploads its log and captured artifacts. See the [collection policy](tracee/policy.yml). |
