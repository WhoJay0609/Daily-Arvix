"""测试 ArXiv 论文时间戳分布"""
from datetime import datetime, timedelta
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import Config
from src.arxiv_client import ArXivClient


def main():
    now = datetime.utcnow()
    cutoff = now - timedelta(days=1)
    print(f"当前 UTC 时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"最近 1 天 cutoff: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分类: {Config.ARXIV_CATEGORIES}")
    print(f"max_results: {Config.ARXIV_MAX_RESULTS}")
    print("-" * 60)

    client = ArXivClient(
        categories=Config.ARXIV_CATEGORIES,
        max_results=Config.ARXIV_MAX_RESULTS
    )

    papers = []
    for category in Config.ARXIV_CATEGORIES:
        category = category.strip()
        fetched = client._fetch_category(category)
        print(f"[{category}] 拉取 {len(fetched)} 篇")
        papers.extend(fetched)

    if not papers:
        print("未拉取到任何论文")
        return

    def _parse_ts(ts: str):
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    print("\n前 20 篇论文时间戳（lastUpdatedDate/Published）:")
    for i, p in enumerate(papers[:20], 1):
        updated = p.updated or p.published
        try:
            updated_dt = _parse_ts(updated)
            delta_hours = (now - updated_dt).total_seconds() / 3600
            recent_flag = "✅" if updated_dt >= cutoff else "❌"
            print(f"{i:02d}. {recent_flag} {updated} ({delta_hours:.1f}h) | {p.title[:80]}")
        except Exception as e:
            print(f"{i:02d}. 解析失败 {updated} | {p.title[:80]} | {e}")


if __name__ == "__main__":
    main()
