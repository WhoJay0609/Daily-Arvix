"""论文历史记录模块"""
from pathlib import Path
from typing import Set
from datetime import datetime

from .config import Config


class PaperHistory:
    """论文历史记录管理"""
    
    def __init__(self, history_file: str = None):
        self.history_file = Path(history_file or Config.HISTORY_FILE)
        self._ensure_file()
    
    def _ensure_file(self):
        """确保历史文件存在"""
        if not self.history_file.exists():
            self.history_file.touch()
    
    def load_history(self) -> Set[str]:
        """加载已处理的论文 ID 集合"""
        if not self.history_file.exists():
            return set()
        
        history = set()
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 格式: arxiv_id|date
                    parts = line.split('|')
                    if parts:
                        history.add(parts[0])
        return history
    
    def save_paper(self, arxiv_id: str):
        """保存单篇论文记录"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"{arxiv_id}|{date_str}\n")
    
    def save_papers(self, arxiv_ids: list):
        """批量保存论文记录"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        with open(self.history_file, 'a', encoding='utf-8') as f:
            for arxiv_id in arxiv_ids:
                f.write(f"{arxiv_id}|{date_str}\n")
    
    def is_processed(self, arxiv_id: str) -> bool:
        """检查论文是否已处理"""
        history = self.load_history()
        return arxiv_id in history
    
    def filter_new_papers(self, papers: list) -> list:
        """过滤出未处理的论文"""
        history = self.load_history()
        new_papers = []
        
        for paper in papers:
            # 从链接中提取 arxiv_id
            arxiv_id = self._extract_arxiv_id(paper.link)
            if arxiv_id and arxiv_id not in history:
                new_papers.append(paper)
        
        return new_papers
    
    def _extract_arxiv_id(self, link: str) -> str:
        """从链接中提取 arxiv ID"""
        # 示例: https://arxiv.org/abs/2401.12345
        if 'arxiv.org' in link:
            parts = link.split('/')
            if 'abs' in parts:
                idx = parts.index('abs')
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        return ""
    
    def get_stats(self) -> dict:
        """获取历史统计信息"""
        if not self.history_file.exists():
            return {"total": 0, "today": 0}
        
        total = 0
        today_count = 0
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    total += 1
                    if today_str in line:
                        today_count += 1
        
        return {"total": total, "today": today_count}
