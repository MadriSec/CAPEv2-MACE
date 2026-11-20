# Windows guest auxiliary modules

The Windows analyzer uses these modules to collect evidence or prepare the guest during a task.

| Source | Role |
| --- | --- |
| [amsi_etw.py](amsi_etw.py) | Records Antimalware Scan Interface events through ETW. |
| [browser.py](browser.py) | Launches a browser during the analysis session. |
| [browsermonitor.py](browsermonitor.py) | Collects request logs produced by the browser extension. |
| [digisig.py](digisig.py) | Runs the Windows signing tool and parses digital signature information. |
| [disguise.py](disguise.py) | Adjusts guest environment details used during analysis. |
| [dns_etw.py](dns_etw.py) | Records Windows DNS events through ETW. |
| [during_script.py](during_script.py) | Runs a supplied script during analysis and captures its output. |
| [evtx.py](evtx.py) | Exports Windows event logs from the guest. |
| [filepickup.py](filepickup.py) | Retrieves a specified guest file at the end of the task. |
| [human.py](human.py) | Simulates user interaction during the analysis session. |
| [network_etw.py](network_etw.py) | Records Windows kernel TCP and UDP events for later process attribution. |
| [permissions.py](permissions.py) | Adjusts access permissions on selected guest paths. |
| [pre_script.py](pre_script.py) | Runs a supplied preparation script before the target starts. |
| [recentfiles.py](recentfiles.py) | Populates the guest with recent files to simulate prior user activity. |
| [screenshots.py](screenshots.py) | Captures guest desktop screenshots during analysis. |
| [sslkeylogfile.py](sslkeylogfile.py) | Collects TLS session keys logged by applications in the guest. |
| [tlsdump.py](tlsdump.py) | Collects TLS master secrets from the Windows security process for traffic analysis. |
| [usage.py](usage.py) | Records CPU and memory usage during the task. |
| [watchdownloads.py](watchdownloads.py) | Watches the downloads directory and uploads files to the host. |
| [wmi_etw.py](wmi_etw.py) | Records Windows Management Instrumentation events through ETW. |
