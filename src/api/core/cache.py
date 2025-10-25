"""
Redis キャッシュ機能
"""
import json
import asyncio
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps

from ..core.logging import get_logger
from ..core.config import load_config

logger = get_logger(__name__)

class CacheManager:
    """Redis キャッシュ管理クラス"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1時間
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _serialize(self, data: Any) -> str:
        """データをシリアライズ"""
        return json.dumps(data, ensure_ascii=False, default=str)
    
    def _deserialize(self, data: str) -> Any:
        """データをデシリアライズ"""
        return json.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return self._deserialize(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """キャッシュに値を設定"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = self._serialize(value)
            ttl = ttl or self.default_ttl
            
            await self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """キャッシュから値を削除"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """キャッシュから取得、なければ関数を実行してキャッシュに保存"""
        # キャッシュから取得を試行
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 関数を実行
        if asyncio.iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)
        
        # キャッシュに保存
        await self.set(key, value, ttl)
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """パターンに一致するキーを削除"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                result = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {result} keys matching pattern: {pattern}")
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0

# グローバルキャッシュマネージャー
cache_manager = CacheManager()

def cache_key(prefix: str, *args, **kwargs) -> str:
    """キャッシュキーを生成"""
    key_parts = [prefix]
    
    # 位置引数を追加
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        elif isinstance(arg, dict):
            key_parts.append(json.dumps(arg, sort_keys=True))
    
    # キーワード引数を追加
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(json.dumps(dict(sorted_kwargs), sort_keys=True))
    
    return ":".join(key_parts)

def cached(ttl: int = 3600, key_prefix: str = ""):
    """キャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # キャッシュキーを生成
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            key = cache_key(prefix, *args, **kwargs)
            
            # キャッシュマネージャーを使用
            async with cache_manager as cache:
                return await cache.get_or_set(key, func, ttl, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同期関数の場合は非同期ラッパーを実行
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # 非同期関数かどうかでラッパーを選択
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class NotionCache:
    """Notion専用キャッシュクラス"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def get_database_pages(self, database_id: str, page_size: int = 100) -> Optional[List[Dict]]:
        """データベースページをキャッシュから取得"""
        key = cache_key("notion:database_pages", database_id, page_size)
        return await self.cache.get(key)
    
    async def set_database_pages(self, database_id: str, pages: List[Dict], ttl: int = 1800) -> bool:
        """データベースページをキャッシュに保存"""
        key = cache_key("notion:database_pages", database_id)
        return await self.cache.set(key, pages, ttl)
    
    async def invalidate_database(self, database_id: str) -> int:
        """データベース関連のキャッシュを無効化"""
        pattern = f"notion:database_pages:{database_id}*"
        return await self.cache.invalidate_pattern(pattern)
    
    async def get_page(self, page_id: str) -> Optional[Dict]:
        """ページをキャッシュから取得"""
        key = cache_key("notion:page", page_id)
        return await self.cache.get(key)
    
    async def set_page(self, page_id: str, page_data: Dict, ttl: int = 3600) -> bool:
        """ページをキャッシュに保存"""
        key = cache_key("notion:page", page_id)
        return await self.cache.set(key, page_data, ttl)
    
    async def invalidate_page(self, page_id: str) -> bool:
        """ページのキャッシュを無効化"""
        key = cache_key("notion:page", page_id)
        return await self.cache.delete(key)
