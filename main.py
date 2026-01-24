"""每日 ArXiv 日报生成器"""
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import Config
from src.arxiv_client import ArXivClient, Paper
from src.llm_client import LLMClient
from src.digest import filter_relevant, sort_by_score, render_daily_digest, get_archive_filename
from src.emailer import send_email, send_wecom_webhook_split
from src.history import PaperHistory
from src.filters import prefilter_papers
from src.cache import LLMCache


def main():
    print("=" * 60)
    print(f"开始生成每日论文日报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not Config.validate():
        print("配置验证失败")
        return

    Config.ensure_output_dir()

    today = datetime.now()
    archive_filename = get_archive_filename(today)
    archive_path = Path(Config.OUTPUT_DIR) / archive_filename

    if archive_path.exists():
        print("\n检测到今日日报已存在，直接读取并推送...")
        digest_content = archive_path.read_text(encoding="utf-8")
        latest_path = Path(Config.OUTPUT_DIR) / "daily_digest.md"
        latest_path.write_text(digest_content, encoding="utf-8")

        subject = f"每日论文日报 - {today.strftime('%Y-%m-%d')}"
        success = False
        wecom_success = False

        if Config.PUSH_CHANNEL in ("email", "both"):
            success = send_email(subject, digest_content, max_retries=3)

        if Config.PUSH_CHANNEL in ("wecom", "both"):
            wecom_success = send_wecom_webhook_split(subject, digest_content, max_retries=3)

        if success or wecom_success:
            print("\n✅ 日报推送成功！")
        else:
            print("\n⚠️  日报已存在，但推送失败")
        print("=" * 60)
        return

    # Step 1: 拉取论文
    print("\n[1/7] 拉取 ArXiv 论文...")
    arxiv_client = ArXivClient(
        categories=Config.ARXIV_CATEGORIES,
        max_results=Config.ARXIV_MAX_RESULTS
    )
    papers = arxiv_client.fetch_recent_papers(days=1)

    if not papers:
        print("未获取到任何论文，退出")
        return
    
    # Step 2: 过滤历史已读论文
    print(f"\n[2/7] 过滤历史已读论文...")
    history = PaperHistory()
    stats = history.get_stats()
    print(f"  历史记录: 共 {stats['total']} 篇，今日已处理 {stats['today']} 篇")
    
    new_papers = history.filter_new_papers(papers)
    print(f"  本次拉取: {len(papers)} 篇，新论文: {len(new_papers)} 篇")
    
    if not new_papers:
        print("没有新论文需要处理，退出")
        return
    
    papers = new_papers

    # Step 3: 关键词预筛选
    print(f"\n[3/7] 关键词预筛选（共 {len(papers)} 篇）...")
    before_filter = len(papers)
    papers = prefilter_papers(
        papers,
        Config.PREFILTER_KEYWORDS,
        Config.PREFILTER_NEGATIVE_KEYWORDS
    )
    if Config.PREFILTER_KEYWORDS or Config.PREFILTER_NEGATIVE_KEYWORDS:
        print(f"  预筛结果: {len(papers)}/{before_filter} 篇")
    else:
        print("  未配置预筛关键词，跳过")
    if not papers:
        print("预筛后无论文需要处理，退出")
        return

    # Step 4: 评分与相关性判断
    print(f"\n[4/7] 评估论文相关性与打分（共 {len(papers)} 篇）...")
    llm_cache = LLMCache(Config.LLM_CACHE_FILE) if Config.LLM_CACHE_ENABLED else None
    llm_client = LLMClient(cache=llm_cache)
    interest_prompt = llm_client.interest_prompt
    scored_papers = []

    max_workers = 5

    def _score_task(paper_item: Paper) -> dict:
        analysis = llm_client.score_and_relevance(paper_item)
        return {
            "paper": paper_item,
            "is_relevant": analysis.get("is_relevant", False),
            "score": analysis.get("score", 0),
            "reason_cn": analysis.get("reason_cn", ""),
            "affiliations": analysis.get("affiliations", [])
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_score_task, paper): paper for paper in papers
        }
        completed = 0
        for future in as_completed(future_map):
            completed += 1
            paper = future_map[future]
            try:
                result = future.result()
                scored_papers.append(result)
            except Exception as e:
                print(f"  [评分失败] {paper.title[:60]}... 错误: {e}")
                scored_papers.append({
                    "paper": paper,
                    "is_relevant": False,
                    "score": 0,
                    "reason_cn": "",
                    "affiliations": []
                })
            print(f"  [评分完成] {completed}/{len(papers)}")

    # Step 5: 过滤相关论文并排序
    print("\n[5/7] 过滤相关论文并按评分排序...")
    relevant_papers = filter_relevant(scored_papers)
    sorted_papers = sort_by_score(relevant_papers)
    
    print(f"  相关论文数量: {len(relevant_papers)}/{len(papers)}")
    if sorted_papers:
        print(f"  最高分: {sorted_papers[0]['score']:.1f}, 最低分: {sorted_papers[-1]['score']:.1f}")
    
    # 记录待保存的历史 ID
    processed_ids = [history._extract_arxiv_id(p.link) for p in papers]
    processed_ids = [pid for pid in processed_ids if pid]

    # Step 6: 生成简短摘要（所有相关论文）
    print("\n[6/7] 生成摘要...")
    def _short_summary_task(item: dict) -> dict:
        paper_item = item["paper"]
        summary = llm_client.short_summary(paper_item)
        item["short_summary"] = summary
        return item

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_short_summary_task, item): item for item in sorted_papers
        }
        completed = 0
        for future in as_completed(future_map):
            completed += 1
            try:
                future.result()
            except Exception as e:
                print(f"  [摘要失败] 错误: {e}")
            print(f"  [摘要完成] {completed}/{len(sorted_papers)}")

    # Step 6.1: TopN 详细摘要
    top_n = max(0, Config.TOP_N_DETAILED)
    top_papers = sorted_papers[:top_n]
    other_papers = sorted_papers[top_n:]

    # TopN 详细摘要
    top_detailed = []
    def _detailed_task(item: dict) -> dict:
        paper_item = item["paper"]
        detailed = llm_client.detailed_summary(paper_item)
        return {
            "paper": paper_item,
            "score": item["score"],
            "reason_cn": item["reason_cn"],
            "affiliations": item.get("affiliations", []),
            "tldr": detailed.get("tldr", ""),
            "background": detailed.get("background", ""),
            "motivation": detailed.get("motivation", ""),
            "method": detailed.get("method", ""),
            "contributions": detailed.get("contributions", ""),
            "limitations": detailed.get("limitations", ""),
            "use_cases": detailed.get("use_cases", ""),
            "summary_cn": detailed.get("summary_cn", "") or item.get("short_summary", "")
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_detailed_task, item): item for item in top_papers
        }
        completed = 0
        for future in as_completed(future_map):
            completed += 1
            item = future_map[future]
            paper = item["paper"]
            try:
                top_detailed.append(future.result())
            except Exception as e:
                print(f"  [详细摘要失败] {paper.title[:50]}... 错误: {e}")
                top_detailed.append({
                    "paper": paper,
                    "score": item["score"],
                    "reason_cn": item["reason_cn"],
                    "affiliations": item.get("affiliations", []),
                    "tldr": "",
                    "background": "",
                    "motivation": "",
                    "method": "",
                    "contributions": "",
                    "limitations": "",
                    "use_cases": "",
                    "summary_cn": item.get("short_summary", "")
                })
            print(f"  [Top完成] {completed}/{len(top_papers)}")

    # 其他简短摘要
    other_short = []
    for i, item in enumerate(other_papers, 1):
        paper = item["paper"]
        other_short.append({
            "paper": paper,
            "score": item["score"],
            "summary_cn": item.get("short_summary", ""),
            "affiliations": item.get("affiliations", [])
        })

    # Step 7: 渲染日报并保存
    print("\n[7/7] 生成日报并发送...")
    digest_content = render_daily_digest(
        top_detailed, 
        other_short, 
        date=today,
        interest_prompt=interest_prompt
    )

    # 保存归档文件
    archive_path.write_text(digest_content, encoding="utf-8")
    print(f"  日报已保存: {archive_path}")

    # 同时保存为 daily_digest.md（最新版本）
    latest_path = Path(Config.OUTPUT_DIR) / "daily_digest.md"
    latest_path.write_text(digest_content, encoding="utf-8")
    print(f"  最新版本: {latest_path}")

    # 发送/推送
    subject = f"每日论文日报 - {today.strftime('%Y-%m-%d')}"
    success = False
    wecom_success = False

    if Config.PUSH_CHANNEL in ("email", "both"):
        success = send_email(subject, digest_content, max_retries=3)

    if Config.PUSH_CHANNEL in ("wecom", "both"):
        wecom_success = send_wecom_webhook_split(subject, digest_content, max_retries=3)

    if success or wecom_success:
        print("\n✅ 日报生成并推送成功！")
    else:
        print("\n⚠️  日报已生成，但推送失败")

    if processed_ids:
        history.save_papers(processed_ids)
        print(f"  已保存 {len(processed_ids)} 篇论文到历史记录")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
