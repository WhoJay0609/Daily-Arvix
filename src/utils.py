"""通用工具函数"""
import hashlib


def extract_arxiv_id(link: str) -> str:
    """从链接中提取 arXiv ID"""
    if not link:
        return ""
    if "arxiv.org" not in link:
        return ""
    parts = link.split("/")
    if "abs" in parts:
        idx = parts.index("abs")
        if idx + 1 < len(parts):
            return parts[idx + 1].split("?")[0]
    if "pdf" in parts:
        idx = parts.index("pdf")
        if idx + 1 < len(parts):
            return parts[idx + 1].replace(".pdf", "").split("?")[0]
    return ""


def build_pdf_link(link: str) -> str:
    """从 arXiv 链接生成 PDF 链接"""
    if not link:
        return ""
    if "/pdf/" in link and link.endswith(".pdf"):
        return link
    if "/abs/" in link:
        base, arxiv_id = link.split("/abs/", 1)
        arxiv_id = arxiv_id.split("?")[0]
        return f"{base}/pdf/{arxiv_id}.pdf"
    return link


def make_cache_key(title: str, published: str, link: str) -> str:
    """生成缓存 key，优先使用 arXiv ID"""
    arxiv_id = extract_arxiv_id(link)
    if arxiv_id:
        return arxiv_id
    raw = f"{title}|{published}|{link}"
    return "fallback_" + hashlib.md5(raw.encode("utf-8")).hexdigest()
