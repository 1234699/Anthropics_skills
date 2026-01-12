"""翻译缓存管理模块"""

import json
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import generate_cache_key


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_entries: int = 0
    hits: int = 0
    misses: int = 0
    size_mb: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """计算命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class TranslationCache(ABC):
    """翻译缓存抽象基类"""
    
    def __init__(self, max_size: int = 10000, ttl: int = 86400):
        """
        初始化缓存
        
        参数:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒），默认24小时
        """
        self.max_size = max_size
        self.ttl = ttl
        self.stats = CacheStats()
    
    @abstractmethod
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> str | None:
        """从缓存获取翻译"""
        pass
    
    @abstractmethod
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str,
        **options: Any
    ) -> None:
        """保存翻译到缓存"""
        pass
    
    @abstractmethod
    def clear(self, pattern: str | None = None) -> int:
        """清除缓存"""
        pass
    
    @abstractmethod
    def stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        pass
    
    def _is_expired(self, timestamp: float) -> bool:
        """检查缓存是否过期"""
        return time.time() - timestamp > self.ttl


class MemoryCache(TranslationCache):
    """内存缓存实现（LRU）"""
    
    def __init__(self, max_size: int = 10000, ttl: int = 86400):
        super().__init__(max_size, ttl)
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
    
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> str | None:
        """从缓存获取翻译"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        
        if key not in self._cache:
            self.stats.misses += 1
            return None
        
        translated, timestamp = self._cache[key]
        
        # 检查是否过期
        if self._is_expired(timestamp):
            del self._cache[key]
            self.stats.misses += 1
            return None
        
        # 移动到末尾（LRU）
        self._cache.move_to_end(key)
        self.stats.hits += 1
        return translated
    
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str,
        **options: Any
    ) -> None:
        """保存翻译到缓存"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        timestamp = time.time()
        
        # 如果已存在，先删除
        if key in self._cache:
            del self._cache[key]
        
        # 如果超过最大大小，删除最旧的
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        # 添加新条目
        self._cache[key] = (translated, timestamp)
        self.stats.total_entries = len(self._cache)
    
    def clear(self, pattern: str | None = None) -> int:
        """清除缓存"""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            self.stats.total_entries = 0
            return count
        
        # 简单的模式匹配（语言对）
        count = 0
        keys_to_delete = []
        for key in self._cache.keys():
            # 这里简化处理，实际应该解析key
            if pattern in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
        
        self.stats.total_entries = len(self._cache)
        return count
    
    def stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_entries": self.stats.total_entries,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate,
            "size_mb": len(json.dumps(dict(self._cache))) / (1024 * 1024),
            "type": "memory",
        }


class FileCache(TranslationCache):
    """文件缓存实现"""
    
    def __init__(
        self,
        cache_dir: str = ".translation_cache",
        max_size: int = 10000,
        ttl: int = 86400
    ):
        super().__init__(max_size, ttl)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.cache_dir / "index.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()
        self._cleanup_expired()
    
    def _load_index(self) -> dict[str, dict[str, Any]]:
        """加载索引文件"""
        if not self._index_file.exists():
            return {}
        
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_index(self) -> None:
        """保存索引文件"""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.txt"
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, metadata in self._index.items():
            if self._is_expired(metadata.get("timestamp", 0)):
                expired_keys.append(key)
        
        for key in expired_keys:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            del self._index[key]
        
        if expired_keys:
            self._save_index()
    
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> str | None:
        """从缓存获取翻译"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        
        if key not in self._index:
            self.stats.misses += 1
            return None
        
        metadata = self._index[key]
        
        # 检查是否过期
        if self._is_expired(metadata.get("timestamp", 0)):
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            del self._index[key]
            self._save_index()
            self.stats.misses += 1
            return None
        
        # 读取缓存文件
        cache_file = self._get_cache_file(key)
        if not cache_file.exists():
            del self._index[key]
            self._save_index()
            self.stats.misses += 1
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                translated = f.read()
            self.stats.hits += 1
            return translated
        except IOError:
            self.stats.misses += 1
            return None
    
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str,
        **options: Any
    ) -> None:
        """保存翻译到缓存"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        timestamp = time.time()
        
        # 如果超过最大大小，删除最旧的
        if len(self._index) >= self.max_size:
            # 按时间戳排序，删除最旧的
            sorted_items = sorted(
                self._index.items(),
                key=lambda x: x[1].get("timestamp", 0)
            )
            oldest_key = sorted_items[0][0]
            cache_file = self._get_cache_file(oldest_key)
            if cache_file.exists():
                cache_file.unlink()
            del self._index[oldest_key]
        
        # 保存到文件
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(translated)
            
            # 更新索引
            self._index[key] = {
                "timestamp": timestamp,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
            self._save_index()
            self.stats.total_entries = len(self._index)
        except IOError:
            pass
    
    def clear(self, pattern: str | None = None) -> int:
        """清除缓存"""
        if pattern is None:
            count = len(self._index)
            # 删除所有缓存文件
            for key in list(self._index.keys()):
                cache_file = self._get_cache_file(key)
                if cache_file.exists():
                    cache_file.unlink()
            self._index.clear()
            self._save_index()
            self.stats.total_entries = 0
            return count
        
        # 模式匹配清除
        count = 0
        keys_to_delete = []
        for key, metadata in self._index.items():
            if pattern in metadata.get("source_lang", "") or pattern in metadata.get("target_lang", ""):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            del self._index[key]
            count += 1
        
        if count > 0:
            self._save_index()
        self.stats.total_entries = len(self._index)
        return count
    
    def stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.txt"):
            total_size += cache_file.stat().st_size
        
        return {
            "total_entries": self.stats.total_entries,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate,
            "size_mb": total_size / (1024 * 1024),
            "type": "file",
            "cache_dir": str(self.cache_dir),
        }


class SQLiteCache(TranslationCache):
    """SQLite数据库缓存实现"""
    
    def __init__(
        self,
        db_path: str = ".translation_cache/cache.db",
        max_size: int = 100000,
        ttl: int = 86400
    ):
        super().__init__(max_size, ttl)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._cleanup_expired()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                cache_key TEXT PRIMARY KEY,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                timestamp REAL NOT NULL,
                options TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON translations(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lang_pair ON translations(source_lang, target_lang)
        """)
        conn.commit()
        conn.close()
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        expired_time = time.time() - self.ttl
        cursor.execute("DELETE FROM translations WHERE timestamp < ?", (expired_time,))
        conn.commit()
        conn.close()
    
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> str | None:
        """从缓存获取翻译"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT translated_text, timestamp FROM translations WHERE cache_key = ?",
            (key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            self.stats.misses += 1
            return None
        
        translated, timestamp = result
        
        # 检查是否过期
        if self._is_expired(timestamp):
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM translations WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            self.stats.misses += 1
            return None
        
        self.stats.hits += 1
        return translated
    
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str,
        **options: Any
    ) -> None:
        """保存翻译到缓存"""
        key = generate_cache_key(text, source_lang, target_lang, **options)
        timestamp = time.time()
        options_json = json.dumps(options) if options else None
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 检查是否超过最大大小
        cursor.execute("SELECT COUNT(*) FROM translations")
        count = cursor.fetchone()[0]
        
        if count >= self.max_size:
            # 删除最旧的条目
            cursor.execute("""
                DELETE FROM translations
                WHERE cache_key = (
                    SELECT cache_key FROM translations
                    ORDER BY timestamp ASC
                    LIMIT 1
                )
            """)
        
        # 插入或更新
        cursor.execute("""
            INSERT OR REPLACE INTO translations
            (cache_key, original_text, translated_text, source_lang, target_lang, timestamp, options)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (key, text, translated, source_lang, target_lang, timestamp, options_json))
        
        conn.commit()
        conn.close()
        self.stats.total_entries = count + 1
    
    def clear(self, pattern: str | None = None) -> int:
        """清除缓存"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if pattern is None:
            cursor.execute("SELECT COUNT(*) FROM translations")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM translations")
        else:
            # 模式匹配（语言对）
            cursor.execute("""
                DELETE FROM translations
                WHERE source_lang LIKE ? OR target_lang LIKE ?
            """, (f"%{pattern}%", f"%{pattern}%"))
            count = cursor.rowcount
        
        conn.commit()
        conn.close()
        self.stats.total_entries = 0
        return count
    
    def stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM translations")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(LENGTH(translated_text)) FROM translations")
        size_bytes = cursor.fetchone()[0] or 0
        conn.close()
        
        return {
            "total_entries": total_entries,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate,
            "size_mb": size_bytes / (1024 * 1024),
            "type": "sqlite",
            "db_path": str(self.db_path),
        }
