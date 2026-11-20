# Reporting modules

After processing and signature evaluation, enabled reporters publish results or manage stored artifacts. The database reporters also share document-building helpers.

| Source | Role |
| --- | --- |
| [bingraph.py](bingraph.py) | Generates visual representations of analyzed binaries. |
| [browserext.py](browserext.py) | Includes events recorded by the browser extension in the report. |
| [callback.py](callback.py) | Sends a completion notification to a configured callback destination. |
| [centralstore.py](centralstore.py) | Uploads artifacts to S3 and associates the analysis with its job ID in central mode. |
| [compression.py](compression.py) | Compresses stored analysis artifacts after processing. |
| [elasticsearchdb.py](elasticsearchdb.py) | Stores processed analysis results in Elasticsearch. |
| [gcs.py](gcs.py) | Uploads analysis files to Google Cloud Storage. |
| [jsondump.py](jsondump.py) | Writes the structured results to a JSON report. |
| [litereport.py](litereport.py) | Writes a smaller report containing selected result sections. |
| [maec41.py](maec41.py) | Exports analysis results in MAEC 4.1 format. |
| [maec5.py](maec5.py) | Exports analysis results in MAEC 5.0 format. |
| [mitre.py](mitre.py) | Builds the MITRE ATT&CK section from recorded techniques. |
| [mongodb.py](mongodb.py) | Stores processed analysis results in MongoDB. |
| [report_doc.py](report_doc.py) | Provides shared helpers for preparing database documents and storing process calls in chunks. |
| [reporthtml.py](reporthtml.py) | Renders the analysis as an HTML report. |
| [tmpfsclean.py](tmpfsclean.py) | Handles retention or removal of the memory dump when using temporary storage. |
