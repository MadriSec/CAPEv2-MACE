# Host auxiliary modules

These modules run alongside a dynamic analysis. The selected collector and network route determine which traffic artifacts reach the analysis directory.

| Source | Role |
| --- | --- |
| [AzSniffer.py](AzSniffer.py) | Starts an Azure packet capture and retrieves the capture file for the task. |
| [Mitmdump.py](Mitmdump.py) | Runs mitmdump during the session to record HTTP exchanges in a HAR file. |
| [PolarProxy.py](PolarProxy.py) | Manages PolarProxy for the task and records decrypted traffic in a packet capture. |
| [QemuScreenshots.py](QemuScreenshots.py) | Periodically captures the QEMU display from the host. |
| [SSLProxy.py](SSLProxy.py) | Manages a per-analysis TLS interception service with STARTTLS support. |
| [sniffer.py](sniffer.py) | Records packets on the analysis network interface using tcpdump. |
