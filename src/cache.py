"""LLM 缓存模块"""
import json
import threading
from datetime import datetime
from pathlib import Path


class LLMCache:
    """基于文件的 LLM 调用缓存"""

    def __init__(self, cache_file: str):
        self.cache_file = Path(cache_file)
        self._lock = threading.Lock()
        self._data = {"version": 1, "papers": {}}
        self._load()

    def _load(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            content = self.cache_file.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, dict) and "papers" in data:
                self._data = data
        except Exception:
            # 读取失败时保持空缓存
            self._data = {"version": 1, "papers": {}}

    def _save(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.cache_file.with_suffix(self.cache_file.suffix + ".tmp")
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.replace(self.cache_file)

    def _touch(self, key: str) -> None:
        entry = self._data["papers"].setdefault(key, {})
        entry["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_score(self, key: str):
        with self._lock:
            return self._data.get("papers", {}).get(key, {}).get("score")

    def set_score(self, key: str, value: dict) -> None:
        with self._lock:
            entry = self._data["papers"].setdefault(key, {})
            entry["score"] = value
            self._touch(key)
            self._save()

    def get_short_summary(self, key: str):
        with self._lock:
            return self._data.get("papers", {}).get(key, {}).get("short_summary")

    def set_short_summary(self, key: str, value: str) -> None:
        with self._lock:
            entry = self._data["papers"].setdefault(key, {})
            entry["short_summary"] = value
            self._touch(key)
            self._save()

    def get_detailed_summary(self, key: str):
        with self._lock:
            return self._data.get("papers", {}).get(key, {}).get("detailed_summary")

    def set_detailed_summary(self, key: str, value: dict) -> None:
        with self._lock:
            entry = self._data["papers"].setdefault(key, {})
            entry["detailed_summary"] = value
            self._touch(key)
            self._save()
