"""
Usage:
--------
python download_commoncrawl.py --max_pages 10
"""
import argparse
import requests, gzip, json, sys, os
from warcio.archiveiterator import ArchiveIterator
import time

import settings
from logger import get_logger

DATA_DIR = settings.DATA_DIR_COMMONCRAWL
CRAWL = "CC-MAIN-2025-43"
BASE_URL = "https://data.commoncrawl.org/"
MAX_RETRIES = 3

logger = get_logger("download_cc", "download_cc.log")

def download_warc_paths():
    url = f"{BASE_URL}crawl-data/{CRAWL}/warc.paths.gz"
    logger.info(f"📥 Downloading WARC paths from {url}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    data = gzip.decompress(r.content)
    return data.decode("utf-8").splitlines()

def iter_warc_records(warc_url, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            with requests.get(warc_url, stream=True, timeout=(30, 600)) as r:
                r.raise_for_status()
                gz = gzip.GzipFile(fileobj=r.raw)
                for record in ArchiveIterator(gz, arc2warc=True):
                    yield record
            return
        except Exception as e:
            logger.warning(f"⚠️  Download failed (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

def extract_response(record):
    if record.rec_type != "response":
        return None
    url = record.rec_headers.get_header("WARC-Target-URI")
    if not url:
        return None
    hdrs = {}
    http = record.http_headers
    if http:
        for k, v in http.headers:
            hdrs[k.lower()] = v
    try:
        body = record.content_stream().read()
    except:
        body = b""
    return {
        "url": url,
        "headers": hdrs,
        "body": body.decode("utf-8", errors="replace")
    }

def main():
    parser = argparse.ArgumentParser(description='Download sample CommonCrawl data.')
    parser.add_argument('--max_pages', default=10, type=int, help='max number of webpages to collect')
    args = parser.parse_args()

    max_pages = args.max_pages

    logger.info("=" * 70)
    logger.info("🚀 Started CommonCrawl download script (Artifact Version)")

    os.makedirs(DATA_DIR, exist_ok=True)
    out_file = os.path.join(DATA_DIR, "sample_records.jsonl")

    paths = download_warc_paths()
    if not paths:
        logger.error("❌ No WARC paths found")
        return

    first_warc = BASE_URL + paths[0]
    logger.info(f"📄 Fetching records from {first_warc}")

    processed_count = 0
    with open(out_file, "w", encoding="utf-8") as f:
        for record in iter_warc_records(first_warc):
            if processed_count >= max_pages:
                break
                
            response = extract_response(record)
            if response:
                f.write(json.dumps({
                    "url": response["url"],
                    "body_length": len(response["body"]),
                    "title_snippet": response["body"][:100].replace('\n', ' ')
                }) + "\n")
                processed_count += 1
                if processed_count % 5 == 0:
                    logger.info(f"✅ Processed {processed_count} webpages...")

    logger.info(f"🎉 Done! Downloaded {processed_count} pages. Saved to {out_file}")

if __name__ == "__main__":
    main()
