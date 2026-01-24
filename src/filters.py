"""预筛选过滤模块"""
from typing import List

from .arxiv_client import Paper


def prefilter_papers(
    papers: List[Paper],
    include_keywords: List[str],
    exclude_keywords: List[str],
) -> List[Paper]:
    """基于关键词进行预筛选（标题+摘要+分类）"""
    include = [kw.strip().lower() for kw in include_keywords if kw and kw.strip()]
    exclude = [kw.strip().lower() for kw in exclude_keywords if kw and kw.strip()]

    if not include and not exclude:
        return papers

    filtered = []
    for paper in papers:
        text = " ".join(
            [
                paper.title or "",
                paper.abstract or "",
                " ".join(paper.categories or []),
            ]
        ).lower()

        if exclude and any(kw in text for kw in exclude):
            continue
        if include and not any(kw in text for kw in include):
            continue
        filtered.append(paper)

    return filtered
