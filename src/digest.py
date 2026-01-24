"""日报渲染与过滤模块"""
from datetime import datetime
from typing import List, Dict, Any

from .arxiv_client import Paper
from .utils import build_pdf_link


def filter_relevant(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤相关论文"""
    return [item for item in results if item.get("is_relevant", False)]


def sort_by_score(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按评分降序排序"""
    return sorted(results, key=lambda x: x.get("score", 0), reverse=True)


def render_daily_digest(
    top5_detailed: List[Dict[str, Any]], 
    other_short: List[Dict[str, Any]], 
    date: datetime = None,
    interest_prompt: str = ""
) -> str:
    """
    生成日报 Markdown 文本
    
    Args:
        top5_detailed: Top5 高分论文（含详细摘要）
        other_short: 其他相关论文（含简短摘要）
        date: 日期
    """
    if date is None:
        date = datetime.now()

    header = f"# 每日论文日报 ({date.strftime('%Y-%m-%d')})\n\n"
    if interest_prompt:
        header += f"**当前关键词**: {interest_prompt}\n\n"
    
    if not top5_detailed and not other_short:
        return header + "今日无相关论文。\n"

    body = ""
    
    # Top5 详细摘要
    if top5_detailed:
        body += "## 📌 重点推荐（Top 5）\n\n"
        for idx, item in enumerate(top5_detailed, 1):
            paper: Paper = item.get("paper")
            score = item.get("score", 0)
            reason = item.get("reason_cn", "")
            background = item.get("background", "")
            motivation = item.get("motivation", "")
            method = item.get("method", "")
            tldr = item.get("tldr", "")
            contributions = item.get("contributions", "")
            limitations = item.get("limitations", "")
            use_cases = item.get("use_cases", "")
            summary = item.get("summary_cn", "")
            authors = ", ".join(paper.authors[:3]) if paper and paper.authors else ""
            if paper and len(paper.authors) > 3:
                authors += " 等"
            affiliations = _format_affiliations(item.get("affiliations"))
            categories = ", ".join(paper.categories) if paper and paper.categories else "未知分类"
            pdf_link = build_pdf_link(paper.link if paper else "")

            body += f"### {idx}. {paper.title if paper else '未知标题'}\n\n"
            body += f"**评分**: {score:.1f}/10  \n"
            body += f"**作者**: {authors}  \n"
            body += f"**单位**: {affiliations}  \n"
            body += f"**分类**: {categories}  \n"
            body += f"**日期**: {paper.published[:10] if paper and paper.published else ''}  \n"
            body += f"**链接**: {paper.link if paper else ''}  \n\n"
            if pdf_link:
                body += f"**PDF**: {pdf_link}  \n\n"
            
            if tldr:
                body += f"**TL;DR**: {tldr}  \n\n"
            if background:
                body += f"**背景**: {background}  \n\n"
            if motivation:
                body += f"**动机**: {motivation}  \n\n"
            if method:
                body += f"**方法**: {method}  \n\n"
            if contributions:
                body += f"**贡献**: {contributions}  \n\n"
            if limitations:
                body += f"**局限**: {limitations}  \n\n"
            if use_cases:
                body += f"**适用场景**: {use_cases}  \n\n"
            if summary:
                body += f"**总结**: {summary}  \n\n"
            if reason:
                body += f"**推荐理由**: {reason}  \n\n"
            
            body += "---\n\n"
    
    # 其他相关论文简短摘要
    if other_short:
        body += "## 📝 其他相关论文\n\n"
        for idx, item in enumerate(other_short, 1):
            paper: Paper = item.get("paper")
            score = item.get("score", 0)
            summary = item.get("summary_cn", "")
            authors = ", ".join(paper.authors[:2]) if paper and paper.authors else ""
            if paper and len(paper.authors) > 2:
                authors += " 等"
            affiliations = _format_affiliations(item.get("affiliations"))
            categories = ", ".join(paper.categories) if paper and paper.categories else "未知分类"
            pdf_link = build_pdf_link(paper.link if paper else "")
            pdf_part = f" | [PDF]({pdf_link})" if pdf_link else ""

            body += f"**{idx}. {paper.title if paper else '未知标题'}**  \n"
            body += (
                f"评分: {score:.1f}/10 | 作者: {authors} | 单位: {affiliations} | "
                f"分类: {categories} | [链接]({paper.link if paper else ''})"
                f"{pdf_part}  \n"
            )
            if summary:
                body += f"{summary}  \n\n"
            else:
                body += "\n"

    return header + body


def _format_affiliations(affiliations: Any) -> str:
    """格式化单位信息"""
    if isinstance(affiliations, list):
        text = ", ".join([str(item).strip() for item in affiliations if str(item).strip()])
        return text if text else "未知单位"
    if isinstance(affiliations, str):
        return affiliations.strip() or "未知单位"
    return "未知单位"


def get_archive_filename(date: datetime = None) -> str:
    """获取归档文件名"""
    if date is None:
        date = datetime.now()
    return f"daily_digest_{date.strftime('%Y-%m-%d')}.md"
