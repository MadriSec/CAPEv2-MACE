# Processing modules

These host-side modules turn stored artifacts into structured results or prepare inputs for other modules. Linux behavior parsing also uses the [platform helpers](platform/PLATFORM_PARSERS.md).

| Source | Role |
| --- | --- |
| [CAPE.py](CAPE.py) | Inspects submitted and captured files, identifies payloads, and associates extracted malware configurations with file hashes. |
| [amsi_etw.py](amsi_etw.py) | Decodes captured AMSI events and interprets their scan results. |
| [analysisinfo.py](analysisinfo.py) | Builds session metadata, including task identity and timing. |
| [antiransomware.py](antiransomware.py) | Counts file extensions and marks overrepresented groups for exclusion from further file processing. |
| [behavior.py](behavior.py) | Builds process records, call summaries, and higher-level behavior from monitor logs. |
| [boxjs.py](boxjs.py) | Uses a Box.js service to analyze script content and retrieve its results. |
| [debug.py](debug.py) | Collects diagnostic information from the analysis logs. |
| [decompression.py](decompression.py) | Restores artifacts compressed by the reporting stage so they can be processed again. |
| [decryptpcap.py](decryptpcap.py) | Produces a decrypted packet capture from recorded TLS traffic and available session secrets. |
| [deduplication.py](deduplication.py) | Identifies duplicate screenshots. |
| [dumptls.py](dumptls.py) | Correlates captured TLS master secrets with session identifiers for use in traffic analysis. |
| [maliciousmacrobot.py](maliciousmacrobot.py) | Analyzes Office macros using MaliciousMacroBot. |
| [memory.py](memory.py) | Runs Volatility analysis on a machine memory dump. |
| [network.py](network.py) | Parses packet captures into network conversations and protocol-level observations. |
| [network_etw.py](network_etw.py) | Attributes Windows network events to processes using ETW records. |
| [pcapng.py](pcapng.py) | Generates a PCAPNG capture during processing. |
| [polarproxy.py](polarproxy.py) | Interprets the decrypted traffic capture produced by PolarProxy. |
| [procmemory.py](procmemory.py) | Examines individual process memory dumps and extracts information about their contents. |
| [procmon.py](procmon.py) | Converts Process Monitor output into individual events. |
| [reversinglabs.py](reversinglabs.py) | Retrieves ReversingLabs intelligence for the analysis target. |
| [script_log_processing.py](script_log_processing.py) | Adds pre-analysis and during-analysis script output to the debug results. |
| [similarity.py](similarity.py) | Submits unidentified artifacts to code similarity services for comparison. |
| [strace.py](strace.py) | Builds Linux process records and a process tree from strace logs. |
| [suricata.py](suricata.py) | Interprets Suricata network inspection output for the report. |
| [threatintelligence.py](threatintelligence.py) | Enriches task results using configured threat intelligence providers. |
| [tracee.py](tracee.py) | Turns guest Tracee logs into structured Linux events and process information. |
| [url_analysis.py](url_analysis.py) | Collects information about a submitted URL. |
| [usage.py](usage.py) | Renders collected resource usage measurements for display in the web report. |
