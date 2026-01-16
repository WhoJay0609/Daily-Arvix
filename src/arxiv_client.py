"""ArXiv API 客户端模块"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import urlencode


class Paper:
    """论文数据类"""
    def __init__(self, title: str, authors: List[str], abstract: str, 
                 link: str, published: str, updated: str, categories: List[str]):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.link = link
        self.published = published
        self.updated = updated
        self.categories = categories
    
    def __repr__(self):
        return f"Paper(title='{self.title[:50]}...', published={self.published})"


class ArXivClient:
    """ArXiv API 客户端"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, categories: List[str], max_results: int = 50):
        self.categories = categories
        self.max_results = max_results
    
    def fetch_recent_papers(self, days: int = 1) -> List[Paper]:
        """
        拉取最近 N 天的论文
        
        Args:
            days: 拉取最近几天的论文，默认1天
            
        Returns:
            论文列表
        """
        all_papers = []
        
        for category in self.categories:
            category = category.strip()
            print(f"正在拉取分类 {category} 的论文...")
            papers = self._fetch_category(category)
            all_papers.extend(papers)
        
        # 过滤最近 N 天的论文
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_papers = []
        
        for paper in all_papers:
            try:
                # 使用 lastUpdatedDate（entry.updated）进行过滤
                target_time = paper.updated or paper.published
                pub_date = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%SZ")
                if pub_date >= cutoff_date:
                    recent_papers.append(paper)
            except Exception as e:
                print(f"解析日期失败: {paper.updated or paper.published}, 错误: {e}")
                # 如果无法解析日期，保守起见仍然包含该论文
                recent_papers.append(paper)
        
        if not recent_papers and all_papers:
            # 若最近 N 天无更新，则回退取最新的若干篇（按 lastUpdatedDate 排序）
            print(f"最近 {days} 天无更新论文，回退取最新 {min(self.max_results, len(all_papers))} 篇")
            recent_papers = all_papers[: self.max_results]

        print(f"共拉取 {len(all_papers)} 篇论文，其中 {len(recent_papers)} 篇是最近 {days} 天内的")
        return recent_papers
    
    def _fetch_category(self, category: str) -> List[Paper]:
        """
        拉取指定分类的论文
        
        Args:
            category: ArXiv 分类，如 'cs.LG'
            
        Returns:
            论文列表
        """
        # 构建查询参数
        query = f"cat:{category}"
        params = {
            'search_query': query,
            'sortBy': 'lastUpdatedDate',
            'sortOrder': 'descending',
            'max_results': self.max_results
        }
        
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        try:
            # 解析 Atom feed
            feed = feedparser.parse(url)
            
            if feed.bozo:
                print(f"警告: Feed 解析出现问题，但会尝试继续: {feed.bozo_exception}")
            
            papers = []
            for entry in feed.entries:
                # 提取论文信息
                title = entry.title.replace('\n', ' ').strip()
                authors = [author.name for author in entry.authors]
                abstract = entry.summary.replace('\n', ' ').strip()
                link = entry.link
                published = entry.published
                updated = entry.updated if hasattr(entry, 'updated') else published
                
                # 提取分类
                categories = []
                if hasattr(entry, 'tags'):
                    categories = [tag.term for tag in entry.tags]
                
                paper = Paper(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    link=link,
                    published=published,
                    updated=updated,
                    categories=categories
                )
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"拉取分类 {category} 时出错: {e}")
            return []
    
    def get_papers_summary(self, papers: List[Paper]) -> str:
        """获取论文摘要信息"""
        if not papers:
            return "未找到任何论文"
        
        summary = f"共 {len(papers)} 篇论文:\n"
        for i, paper in enumerate(papers[:5], 1):
            summary += f"{i}. {paper.title}\n"
        if len(papers) > 5:
            summary += f"... 还有 {len(papers) - 5} 篇\n"
        
        return summary
