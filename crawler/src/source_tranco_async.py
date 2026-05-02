import asyncio
import os
from typing import List
from tranco import Tranco

from tortoise.exceptions import IntegrityError

from database.model.sites import Site
from database.db import init_db, close_db


class TrancoHelper(object):
    def __init__(self):
        self.ranking = Tranco(cache=True, cache_dir='/tmp/.tranco')
        self.ranking_list = self.ranking.list(list_id="8LZ3V")
        self.tranco_top_list: List[str] = self.ranking_list.top()


async def add_site(site_name, rank, url):
    try:
        site = await Site.create(
            site=site_name,
            rank=rank,
            url=url,
            experiment_headers_state="free",
            experiment_inclusions_state="free",
            experiment_cxss_state="free",
            experiment_pmsecurity_state="free",
        )
        return site
    except IntegrityError:
        print(f"Site with rank {rank} already exists. Skipping...")
        return None


async def main():
    await init_db()

    crawler_id = int(os.environ.get('CRAWLER_ID', 0))
    
    sites_per_crawler = 10000
    
    start = crawler_id * sites_per_crawler + 1  # 排名从 1 开始
    end = start + sites_per_crawler - 1
    
    start = max(1, start)
    
    print(f"CRAWLER_ID: {crawler_id}, process range: {start} - {end}")
    
    length = end - start + 1

    tranco_helper = TrancoHelper()
    tasks = [] 

    for i in range(start - 1, end):
        if i >= len(tranco_helper.tranco_top_list):
            print(f"WARN: ID {i}  tranco_top_list length is exceeded.")
            break
            
        site_name = tranco_helper.tranco_top_list[i]
        rank = tranco_helper.ranking_list.rank(site_name)
        url = f"http://{site_name}"

        tasks.append(add_site(site_name, rank, url))

    results = await asyncio.gather(*tasks)

    added_count = sum(1 for result in results if result is not None)
    print(f"Successfully {added_count}/{length} websites added to the database.")

    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
