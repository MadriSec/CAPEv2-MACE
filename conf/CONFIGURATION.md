# Reading the effective configuration

The `Config` class builds an ordered list of configuration files. Normally it reads `conf/default/<name>.conf.default`, then `conf/<name>.conf`, followed by the fragments in `conf/<name>.conf.d/*.conf` in alphabetical order. Overrides from the custom configuration directory follow. When set, `CAPE_CD` also contributes configuration files. Later files can override individual options from earlier ones. [Configuration loader](../lib/cuckoo/common/config.py) · [Directory conventions](readme.md)

| Question | Where to start |
| --- | --- |
| Which backend manages the machines? | [cuckoo.conf.default](default/cuckoo.conf.default) and the selected machinery configuration |
| Which network route is configured? | [routing.conf.default](default/routing.conf.default) |
| Which auxiliary collectors are enabled? | [auxiliary.conf.default](default/auxiliary.conf.default) |
| Which modules interpret the artifacts? | [processing.conf.default](default/processing.conf.default) |
| Where are results published? | [reporting.conf.default](default/reporting.conf.default) |

To reconstruct a particular run, check its submission options as well. GuestManager prepares a task-specific `analysis.conf` for the guest. Tracee collection, for example, depends on the options the guest receives and the tools installed on the analysis machine.
