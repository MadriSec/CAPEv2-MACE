# Windows analysis packages

Each package selects the application or runtime used to open a target inside the analysis guest.

| Source | Role |
| --- | --- |
| [Ie4uinit.py](Ie4uinit.py) | Analyzes an INF target using the Windows IE initialization utility. |
| [access.py](access.py) | Opens an .accdr file using MSACCESS.EXE. |
| [applet.py](applet.py) | Opens a java applet using firefox (or iexplore). |
| [archive.py](archive.py) | Looks for executables inside an archive. |
| [autoit.py](autoit.py) | Executes the sample with autoit3. |
| [batch.py](batch.py) | Executes the batch scripts with cmd.exe. |
| [chm.py](chm.py) | Opens the compiled help file with hh.exe. |
| [chrome.py](chrome.py) | Opens the URL in Google Chrome. |
| [chromium.py](chromium.py) | Opens the URL in Chromium. |
| [chromium_ext.py](chromium_ext.py) | Opens the URL in Chromium with loaded extension. |
| [cpl.py](cpl.py) | Opens the sample using the control panel. |
| [crx.py](crx.py) | Loads a CRX file as a Chrome extension. |
| [dll.py](dll.py) | Executes a .DLL file using rundll32.exe. |
| [doc.py](doc.py) | Opens a document file with WINWORD.EXE. |
| [doc2016.py](doc2016.py) | Opens a document in Word 2016. |
| [doc_antivm.py](doc_antivm.py) | Opens a Word document with guest environment adjustments. |
| [edge.py](edge.py) | Opens the URL in Microsoft Edge. |
| [eml.py](eml.py) | Opens an email file with MS Outlook. |
| [exe.py](exe.py) | Runs the supplied executable. |
| [firefox.py](firefox.py) | Opens the URL in firefox. |
| [firefox_ext.py](firefox_ext.py) | Opens the URL in Firefox with an analysis extension. |
| [generic.py](generic.py) | Executes the sample file with cmd.exe. |
| [hta.py](hta.py) | Executes the sample with mshta.exe. |
| [hwp.py](hwp.py) | Opens a document with Hangul Word Processor. |
| [ichitaro.py](ichitaro.py) | Opens a .jtd file using Ichitaro viewer. |
| [ie.py](ie.py) | Opens the URL in Internet Explorer. |
| [inf.py](inf.py) | Opens the sample with cmstp.exe. |
| [inp.py](inp.py) | Opens a .inp file using InPage Urdu Professional. |
| [jar.py](jar.py) | Executes a .jar file using javaw.exe (or java.exe). |
| [js.py](js.py) | Executes a .JS file using wscript.exe. |
| [js_antivm.py](js_antivm.py) | Runs JavaScript through Windows Script Host with guest environment adjustments. |
| [lnk.py](lnk.py) | Opens a Windows shortcut in the guest. |
| [mht.py](mht.py) | Opens a .mht file with Internet Explorer. |
| [msbuild.py](msbuild.py) | Opens a dotnet project file with MSBuild. |
| [msg.py](msg.py) | Opens a .msg file with MS Outlook. |
| [msi.py](msi.py) | Executes a sample with msiexec.exe. |
| [msix.py](msix.py) | Executes a sample .msix file with powershell. |
| [nodejs.py](nodejs.py) | Executes a JS sample using NodeJS. |
| [nsis.py](nsis.py) | Runs a submitted NSIS installer. |
| [ollydbg.py](ollydbg.py) | Opens the sample with OllyDbg. |
| [one.py](one.py) | Opens a sample file with ONENOTE.EXE. |
| [pdf.py](pdf.py) | Opens .pdf file with Adobe Reader / Acrobat. |
| [ppt.py](ppt.py) | Opens sample file with Powerpoint. |
| [ppt2016.py](ppt2016.py) | Opens a presentation using the Office 2016 PowerPoint executable. |
| [ps1.py](ps1.py) | Executes a sample file with powershell. |
| [pub.py](pub.py) | Opens a .pub file with MS Publisher. |
| [pub2016.py](pub2016.py) | Opens a publication using the Office 2016 Publisher executable. |
| [python.py](python.py) | Executes sample file with python. |
| [rar.py](rar.py) | Extracts a RAR archive and starts the selected member. |
| [rdp.py](rdp.py) | Opens the submitted Remote Desktop connection file. |
| [reg.py](reg.py) | Opens a registry file with reg.exe. |
| [regsvr.py](regsvr.py) | Opens the file with regsvr32.exe. |
| [sct.py](sct.py) | Opens a Windows scriptlet for analysis. |
| [service.py](service.py) | Launches the given sample as a service. |
| [service_dll.py](service_dll.py) | Loads a service DLL as a Windows service for observation. |
| [shellcode.py](shellcode.py) | Observes a 32-bit raw code sample using the guest analysis loader. |
| [shellcode_x64.py](shellcode_x64.py) | Observes a 64-bit raw code sample using the guest analysis loader. |
| [swf.py](swf.py) | Opens an .swf file using flashplayer.exe. |
| [tor_browser.py](tor_browser.py) | Opens the target URL in Tor Browser. |
| [vbejse.py](vbejse.py) | Runs encoded Windows scripts using Windows Script Host. |
| [vbs.py](vbs.py) | Executes a .vbs (or .vbe) file using wscript.exe. |
| [wsf.py](wsf.py) | Executes a .wsf file using wscript.exe. |
| [xls.py](xls.py) | Opens the supplied document with EXCEL.EXE. |
| [xls2016.py](xls2016.py) | Opens a workbook in Excel 2016. |
| [xps.py](xps.py) | Opens the sample file with xpsrchvw.exe. |
| [xslt.py](xslt.py) | Opens sample file using wmic.exe. |
| [zip.py](zip.py) | Extracts a ZIP archive and starts the selected member. |
| [zip_compound.py](zip_compound.py) | Extracts a multi-file ZIP submission and prepares the selected target with companion files. |
