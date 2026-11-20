# Behavioral signatures

Signature modules inspect collected evidence for reportable findings. One Python module can define several signatures. The all, linux, and windows subpackages in this checkout contain package initializers only.

| Source | Role |
| --- | --- |
| [CAPE.py](CAPE.py) | Groups signatures for behaviors such as unpacking, decryption, and process injection. |
| [cape_extracted.py](cape_extracted.py) | Reports extracted payload content and malware configurations recorded by CAPE. |
| [https.py](https.py) | Collects distinct URLs seen in InternetOpenUrl calls and records them as signature evidence. |
| [qr_urls.py](qr_urls.py) | Reports URLs that earlier analysis extracted from QR codes in screenshots. |
