# Linux analysis packages

The selected package prepares the target and chooses the program that opens or executes it inside the guest.

| Source | Role |
| --- | --- |
| [archive.py](archive.py) | Extracts archive members and selects files for analysis. |
| [bash.py](bash.py) | Runs a submitted shell script with Bash. |
| [deb.py](deb.py) | Installs the submitted Debian package with dpkg. |
| [doc.py](doc.py) | Opens a document in LibreOffice Writer. |
| [firefox.py](firefox.py) | Opens the target in Firefox. |
| [generic.py](generic.py) | Marks the target executable and launches it through the shell. |
| [jar.py](jar.py) | Launches Java with the submitted archive or the requested class. |
| [js.py](js.py) | Runs JavaScript using Node.js. |
| [pdf.py](pdf.py) | Opens a PDF in Xpdf. |
| [perl.py](perl.py) | Runs a Perl script using the guest interpreter. |
| [ps1.py](ps1.py) | Runs a PowerShell script using pwsh. |
| [python.py](python.py) | Runs a Python script using Python 3. |
| [python_whl.py](python_whl.py) | Installs a submitted Python wheel using pip. |
| [wget.py](wget.py) | Downloads a target and delegates analysis to the package selected for that file. |
| [xdg_open.py](xdg_open.py) | Opens the target with its registered desktop application. |
| [zip.py](zip.py) | Unpacks a ZIP file and selects an extracted target for analysis. |
