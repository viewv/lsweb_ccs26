import argparse
import asyncio
import csv
import os
from typing import List, Dict

from tortoise.exceptions import IntegrityError

from database.model.sites import Site
from database.db import init_db, close_db

async def add_site(site_name: str, rank: int, url: str):
    try:
        # Create a new Site instance and insert it into the database
        site = await Site.create(
            site=site_name,
            rank=rank,
            url=url,
            experiment_headers_state="free",
            experiment_inclusions_state="free",
            experiment_cxss_state="free",
            experiment_pmsecurity_state="free",
        )
        return site  # Return the created Site instance
    except IntegrityError:
        # Handle unique constraint violation
        print(f"Site with rank {rank} already exists. Skipping...")
        return None  # Or return a specific error message


async def main():
    parser = argparse.ArgumentParser(description="Seed the crawler database with a list of domains from a CSV file.")
    parser.add_argument("--csv", type=str, default="example.csv", help="Path to the input CSV file containing 'rank' and 'domain' columns.")
    args = parser.parse_args()

    csv_path = args.csv

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    await init_db()

    example_sites = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row.get("domain", "").strip()
                rank_str = row.get("rank", "").strip()
                
                if domain and rank_str.isdigit():
                    example_sites.append({
                        "domain": domain,
                        "url": f"http://{domain}",
                        "rank": int(rank_str)
                    })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        await close_db()
        return
    
    print(f"Processing simple example ranking list from {csv_path}. Total sites: {len(example_sites)}")
    
    tasks = []  # Create a task list
    
    for site_data in example_sites:
        domain = site_data['domain']
        url = site_data['url']
        rank = site_data['rank']

        # Add tasks to the list
        tasks.append(add_site(domain, rank, url))

    if not tasks:
        print("No valid sites found in the CSV.")
    else:
        # Execute all tasks in parallel using asyncio.gather
        results = await asyncio.gather(*tasks)

        added_count = sum(1 for result in results if result is not None)
        print(f"Successfully added {added_count}/{len(example_sites)} websites to the database.")

    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
