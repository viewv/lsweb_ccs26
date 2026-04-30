import asyncio
import os
from typing import List
from tranco import Tranco

from tortoise.exceptions import IntegrityError

from database.model.sites import Site
from database.db import init_db, close_db


class TrancoHelper(object):
    def __init__(self):
        self.ranking = Tranco(cache=True, cache_dir='.tranco')
        # self.ranking_list = self.ranking.list(list_id="663NX")
        self.ranking_list = self.ranking.list(list_id="8LZ3V")
        self.tranco_top_list: List[str] = self.ranking_list.top()


async def add_site(site_name, rank, url):
    try:
        # 创建新的 Site 实例并插入到数据库
        site = await Site.create(
            site=site_name,
            rank=rank,
            url=url,
            experiment_headers_state="free",
            experiment_inclusions_state="free",
            experiment_cxss_state="free",
            experiment_pmsecurity_state="free",
        )
        return site  # 返回创建的 Site 实例
    except IntegrityError:
        # 处理唯一性约束错误
        print(f"Site with rank {rank} already exists. Skipping...")
        return None  # 或者返回一个特定的错误信息


async def main():
    await init_db()

    # 从环境变量获取 CRAWLER_ID，如果未设置则默认为 0
    crawler_id = int(os.environ.get('CRAWLER_ID', 0))
    
    # 每个爬虫处理 10,000 个网站
    sites_per_crawler = 10000
    
    # 计算当前爬虫的起始和结束位置
    start = crawler_id * sites_per_crawler + 1  # 排名从 1 开始
    end = start + sites_per_crawler - 1
    
    # 确保 start 至少为 1
    start = max(1, start)
    
    print(f"CRAWLER_ID: {crawler_id}, 处理排名范围: {start} - {end}")
    
    length = end - start + 1

    tranco_helper = TrancoHelper()
    tasks = []  # 创建一个任务列表

    # 注意：tranco_top_list 的索引从 0 开始，而排名从 1 开始
    # 因此需要将 start 和 end 减 1 来获取正确的索引
    for i in range(start - 1, end):
        if i >= len(tranco_helper.tranco_top_list):
            print(f"警告: 索引 {i} 超出了 tranco_top_list 的范围")
            break
            
        site_name = tranco_helper.tranco_top_list[i]
        rank = tranco_helper.ranking_list.rank(site_name)
        url = f"http://{site_name}"

        # 将任务添加到列表中
        tasks.append(add_site(site_name, rank, url))

    # 使用 asyncio.gather 并行执行所有任务
    results = await asyncio.gather(*tasks)

    added_count = sum(1 for result in results if result is not None)
    print(f"Successfully {added_count}/{length} websites added to the database.")

    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
