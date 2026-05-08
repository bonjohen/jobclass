# Extract Patterns for Government APIs

## The Lesson

Federal data sources are not designed for programmatic access. They block bare HTTP requests, publish in heterogeneous formats, embed preamble rows in spreadsheets, and experience periodic outages around major releases. A robust extract layer must handle all of these realities with browser-like headers, format-specific conversion chains, preamble detection, retry logic, and immutable raw storage.

## Context

A labor market data pipeline downloaded data from BLS, O*NET, and SOC — all federal agencies publishing periodic data releases as downloadable files. A plain `requests.get(url)` to BLS.gov returned `403 Forbidden`. OEWS data arrived as XLSX inside ZIP archives. BLS XLSX files started with 2-4 rows of agency preamble before the actual header. Some text files included invisible BOM characters. The pipeline needed a single extract layer that could reliably handle all of these sources.

## What Happened

1. **Browser-like headers were added to all requests.** BLS.gov rejects requests without `Sec-Fetch-*` headers. The `User-Agent` alone is not sufficient — the server specifically checks for `Sec-Fetch-Dest: document` and `Sec-Fetch-Mode: navigate`:

   ```python
   headers = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; ...) Chrome/131.0.0.0",
       "Accept": "text/html,application/xhtml+xml,...",
       "Sec-Fetch-Dest": "document",
       "Sec-Fetch-Mode": "navigate",
       "Sec-Fetch-Site": "none",
       "Sec-Fetch-User": "?1",
       "Upgrade-Insecure-Requests": "1",
   }
   ```

   Many federal data sites (Census, EPA, USDA) apply similar filtering. The pipeline uses a single set of browser-like headers for all government sources.

2. **Retry with exponential backoff was implemented.** 5xx errors and timeouts are transient — the server may recover. 4xx errors are permanent — retrying will not help. The first retry waits 1 second, the second 2 seconds, the third 4 seconds:

   ```python
   for attempt in range(max_retries + 1):
       try:
           response = client.get(url)
           if 200 <= response.status_code < 300:
               return result
           if response.status_code >= 500 and attempt < max_retries:
               time.sleep(backoff * (2 ** attempt))
               continue
           raise DownloadError()
       except TimeoutException:
           if attempt < max_retries:
               time.sleep(backoff * (2 ** attempt))
               continue
           raise
   ```

3. **A format-specific conversion chain normalized all sources to CSV text.** Each source arrives in a different format, but every parser expects CSV:

   ```python
   def convert_to_text(data, expected_format, sheet_name=None):
       if expected_format in ("csv", "tsv", "text"):
           return data.decode("utf-8-sig")
       elif expected_format == "xlsx_in_zip":
           xlsx_bytes = extract_xlsx_from_zip(data)
           return xlsx_to_csv(xlsx_bytes)
       elif expected_format == "xlsx":
           return xlsx_to_csv(data, sheet_name)
   ```

   | Source | Format | Conversion Chain |
   |---|---|---|
   | OEWS | xlsx_in_zip | ZIP -> XLSX -> CSV |
   | SOC 2018 | xlsx | XLSX -> CSV |
   | O*NET | tsv | decode UTF-8 |
   | BLS Projections | xlsx | XLSX -> CSV |
   | BLS CPI-U | text | decode UTF-8 |

   The `utf-8-sig` encoding handles the BOM (byte order mark) that some government tools insert at the start of text files. Standard `utf-8` decoding would preserve the BOM as an invisible character in the first column name, causing downstream lookups to fail silently.

4. **Preamble detection was added for BLS XLSX files.** The parser scans the first 20 rows and picks the first row with at least 3 non-empty cells:

   ```python
   def _find_header_row(worksheet, max_scan=20):
       for i, row in enumerate(worksheet.iter_rows(...), start=1):
           non_none = [c for c in row if c is not None]
           if len(non_none) >= 3:
               return i
       return 1
   ```

5. **A declarative manifest replaced hard-coded download logic.** All download URLs, formats, and parser routing live in a single YAML file. Adding a new data source means adding one entry:

   ```python
   @dataclass
   class ManifestEntry:
       source_name: str
       dataset_name: str
       dataset_url: str
       expected_format: str
       parser_name: str
       sheet_name: str | None
       enabled: bool = True
   ```

6. **An immutable raw storage contract was enforced.** Every downloaded artifact gets a SHA-256 checksum, UTC timestamp, and original URL recorded. Raw bytes are preserved at `raw/{source_name}/{dataset_name}/{source_release_id}/{run_id}/{original_file_name}`. Two downloads of the same dataset with different release IDs are stored side by side, not overwritten.

## Key Insights

- **The `Sec-Fetch-*` headers are the key to government sites, not just `User-Agent`.** Many federal servers specifically check for the header combination that indicates a real browser page load. A `User-Agent` string alone is not sufficient.
- **Distinguish retryable from non-retryable errors.** A `404 Not Found` means the URL is wrong — waiting longer will not make it appear. A `503 Service Unavailable` means the server is temporarily overloaded and will likely recover. Treating all errors the same wastes time on permanent failures and gives up too quickly on transient ones.
- **Raw immutability pays for itself on parser bugs.** When a parser bug is discovered, the fix can be tested against the exact bytes that exposed the bug without waiting for a fresh download. The pipeline can be re-run from the parse step forward, skipping the download entirely.
- **A manifest is both configuration and documentation.** Anyone reading the YAML file can see every external dependency at a glance — which URLs the pipeline contacts, what format each file uses, and how data flows into the parsing layer.
- **BOM handling is invisible but critical.** The `utf-8-sig` encoding strips the byte order mark automatically. Standard `utf-8` would preserve it as an invisible character in the first column name, causing silent lookup failures downstream.

## Related Lessons

- [Schema Drift Detection](14-schema-drift.md)
- [Idempotent Pipelines](07-idempotent-pipelines.md)
- [Federal Data Landscape](02-federal-data-landscape.md)
