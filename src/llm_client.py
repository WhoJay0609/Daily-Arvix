"""LLM API 客户端模块（OpenAI Compatible）"""
import json
import re
import time
from typing import Dict, Any

from openai import OpenAI

from .config import Config
from .arxiv_client import Paper
from .utils import make_cache_key


class LLMClient:
    """LLM API 客户端"""

    def __init__(self, cache=None):
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
        self.model = Config.OPENAI_MODEL
        self.interest_prompt = Config.get_interest_prompt()
        self.cache = cache

    def _get_cache_key(self, paper: Paper) -> str:
        return make_cache_key(paper.title, paper.published, paper.link)

    def score_and_relevance(self, paper: Paper, max_retries: int = 3) -> Dict[str, Any]:
        """
        判断论文相关性并打分
        
        Returns:
            dict: {is_relevant, score, reason_cn}
        """
        system_prompt = (
            "你是科研助理，擅长快速评估论文与研究兴趣的相关性。"
            "请严格输出 JSON，不要输出其他内容。"
        )

        user_prompt = f"""
请根据以下兴趣方向，判断论文是否相关并打分，并尽量抽取作者所属单位：

兴趣方向：
{self.interest_prompt}

论文信息：
标题：{paper.title}
作者：{', '.join(paper.authors)}
摘要：{paper.abstract}

输出格式（严格 JSON）：
{{
  "is_relevant": <true/false，是否与兴趣方向相关>,
  "score": <0-10 的数字，相关性与质量综合评分>,
  "reason_cn": "<简短理由，1-2句>",
  "affiliations": ["<作者所属单位1>", "<作者所属单位2>"]
}}
""".strip()

        cache_key = self._get_cache_key(paper)
        if self.cache:
            cached = self.cache.get_score(cache_key)
            if cached is not None:
                return cached

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )

                content = response.choices[0].message.content.strip()
                parsed = self._parse_json(content)

                is_relevant = parsed.get("is_relevant", False)
                score = parsed.get("score", 0)
                reason = parsed.get("reason_cn", "").strip()
                affiliations = self._normalize_affiliations(parsed.get("affiliations", []))

                try:
                    score = float(score)
                except Exception:
                    score = 0

                result = {
                    "is_relevant": bool(is_relevant),
                    "score": score,
                    "reason_cn": reason,
                    "affiliations": affiliations
                }
                if self.cache:
                    self.cache.set_score(cache_key, result)
                return result

            except Exception as e:
                print(f"评分调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return {
                        "is_relevant": False,
                        "score": 0,
                        "reason_cn": "",
                        "affiliations": []
                    }

    def detailed_summary(self, paper: Paper, max_retries: int = 3) -> Dict[str, Any]:
        """
        生成详细摘要（Top5 用）
        
        Returns:
            dict: {tldr, background, motivation, method, contributions, limitations, use_cases, summary_cn}
        """
        system_prompt = (
            "你是科研助理，擅长深入分析论文并提取关键信息。"
            "请严格输出 JSON，不要输出其他内容。"
        )

        user_prompt = f"""
请详细分析以下论文，提取关键信息，所有输出内容必须为中文：

论文信息：
标题：{paper.title}
作者：{', '.join(paper.authors)}
摘要：{paper.abstract}

输出格式（严格 JSON）：
{{
  "tldr": "<一句话总结核心结论，中文>",
  "background": "<研究背景，2-3句，中文>",
  "motivation": "<研究动机与要解决的问题，2-3句，中文>",
  "method": "<主要方法与技术，2-3句，中文>",
  "contributions": "<主要贡献点，2-3条，中文>",
  "limitations": "<局限性或风险点，1-2条，中文>",
  "use_cases": "<适用场景或潜在应用，1-2条，中文>",
  "summary_cn": "<总结，1-2句，中文>"
}}
""".strip()

        cache_key = self._get_cache_key(paper)
        if self.cache:
            cached = self.cache.get_detailed_summary(cache_key)
            if cached is not None:
                return cached

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )

                content = response.choices[0].message.content.strip()
                parsed = self._parse_json(content)

                result = {
                    "tldr": parsed.get("tldr", "").strip(),
                    "background": parsed.get("background", "").strip(),
                    "motivation": parsed.get("motivation", "").strip(),
                    "method": parsed.get("method", "").strip(),
                    "contributions": parsed.get("contributions", "").strip(),
                    "limitations": parsed.get("limitations", "").strip(),
                    "use_cases": parsed.get("use_cases", "").strip(),
                    "summary_cn": parsed.get("summary_cn", "").strip()
                }
                if self.cache and any(result.values()):
                    self.cache.set_detailed_summary(cache_key, result)
                return result

            except Exception as e:
                print(f"详细摘要调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {
                        "tldr": "",
                        "background": "",
                        "motivation": "",
                        "method": "",
                        "contributions": "",
                        "limitations": "",
                        "use_cases": "",
                        "summary_cn": ""
                    }

    def short_summary(self, paper: Paper, max_retries: int = 3) -> str:
        """
        生成简短摘要（其余相关论文用）
        
        Returns:
            str: 简短中文摘要
        """
        system_prompt = (
            "你是科研助理，擅长用一两句话概括论文核心内容。"
            "请严格输出 JSON，不要输出其他内容。"
        )

        user_prompt = f"""
请用1-2句话简短概括论文核心内容（中文）：

论文信息：
标题：{paper.title}
摘要：{paper.abstract}

输出格式（严格 JSON）：
{{
  "summary_cn": "<简短摘要，1-2句，中文>"
}}
""".strip()

        cache_key = self._get_cache_key(paper)
        if self.cache:
            cached = self.cache.get_short_summary(cache_key)
            if cached is not None:
                return cached

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )

                content = response.choices[0].message.content.strip()
                parsed = self._parse_json(content)

                summary = parsed.get("summary_cn", "").strip()
                if summary and self.cache:
                    self.cache.set_short_summary(cache_key, summary)
                return summary

            except Exception as e:
                print(f"简短摘要调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return ""

    def _normalize_affiliations(self, affiliations: Any) -> list:
        """标准化单位列表"""
        if isinstance(affiliations, list):
            return [str(item).strip() for item in affiliations if str(item).strip()]
        if isinstance(affiliations, str):
            text = affiliations.strip()
            return [text] if text else []
        return []

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """解析 JSON 输出，容错处理"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 解析失败返回空结构
        return {}
