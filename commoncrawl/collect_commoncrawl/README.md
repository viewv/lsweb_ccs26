# CommonCrawl Downloader (Artifact Version)

This directory contains a simplified version of the CommonCrawl data downloader, adapted specifically for the artifact review process. All personal information, hardcoded cluster paths, and complex distributed task processing (e.g., Celery) have been removed.

The goal of this module is to demonstrate how we fetch raw CommonCrawl WARC files, parse them, and extract the relevant HTML bodies for prompt injection analysis.

## Requirements

The core dependencies for this script are `requests` and `warcio`.

```bash
pip install requests warcio
```

## Usage

You can run the standalone Python script to download a small sample of CommonCrawl records. It will connect to the `data.commoncrawl.org` endpoint, retrieve the latest paths, and stream the WARC file to extract the HTML content.

```bash
python download_commoncrawl.py --max_pages 10
```

### Parameters:
- `--max_pages`: The maximum number of pages to extract and download (default is 10). Setting a low number is recommended for testing, as WARC files are extremely large.

## Output

The script creates an `outputs/commoncrawl` directory (by default in `/tmp/crawler_outputs` or your environment's root dir) and saves the downloaded data as a JSON Lines (`.jsonl`) file named `sample_records.jsonl`.

Each line in the file represents one webpage and contains:
- `url`: The URL of the crawled webpage
- `body_length`: The length of the HTML body
- `title_snippet`: A short snippet of the webpage content
