#!/usr/bin/env python3
"""
PRISM Performance Optimization Module
パフォーマンス最適化モジュール
"""

import asyncio
import time
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import psutil
import gc

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    request_count: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    last_updated: datetime = None

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.start_time = time.time()
        
    def record_request(self, endpoint: str, response_time: float):
        """リクエストを記録"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = PerformanceMetrics()
            
        metrics = self.metrics[endpoint]
        metrics.request_count += 1
        metrics.total_response_time += response_time
        metrics.min_response_time = min(metrics.min_response_time, response_time)
        metrics.max_response_time = max(metrics.max_response_time, response_time)
        metrics.avg_response_time = metrics.total_response_time / metrics.request_count
        metrics.last_updated = datetime.now()
        
    def get_system_metrics(self) -> Dict[str, float]:
        """システムメトリクスを取得"""
        process = psutil.Process()
        return {
            "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "open_files": len(process.open_files()),
            "threads": process.num_threads(),
            "uptime_seconds": time.time() - self.start_time
        }
    
    def get_endpoint_metrics(self, endpoint: str) -> Optional[PerformanceMetrics]:
        """エンドポイントメトリクスを取得"""
        return self.metrics.get(endpoint)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """全メトリクスを取得"""
        return {
            "system": self.get_system_metrics(),
            "endpoints": {k: {
                "request_count": v.request_count,
                "avg_response_time": v.avg_response_time,
                "min_response_time": v.min_response_time,
                "max_response_time": v.max_response_time,
                "last_updated": v.last_updated.isoformat() if v.last_updated else None
            } for k, v in self.metrics.items()}
        }

# グローバルパフォーマンス監視インスタンス
performance_monitor = PerformanceMonitor()

def performance_timer(endpoint: str = None):
    """パフォーマンス計測デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                response_time = time.time() - start_time
                ep = endpoint or f"{func.__module__}.{func.__name__}"
                performance_monitor.record_request(ep, response_time)
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                response_time = time.time() - start_time
                ep = endpoint or f"{func.__module__}.{func.__name__}"
                performance_monitor.record_request(ep, response_time)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class ConnectionPool:
    """接続プール管理クラス"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections: Dict[str, List[Any]] = {}
        self.connection_counts: Dict[str, int] = {}
        
    async def get_connection(self, service: str, connection_factory: Callable):
        """接続を取得"""
        if service not in self.active_connections:
            self.active_connections[service] = []
            self.connection_counts[service] = 0
            
        if self.active_connections[service]:
            return self.active_connections[service].pop()
            
        if self.connection_counts[service] < self.max_connections:
            connection = await connection_factory()
            self.connection_counts[service] += 1
            return connection
            
        # 最大接続数に達した場合、新しい接続を作成
        return await connection_factory()
    
    async def return_connection(self, service: str, connection: Any):
        """接続を返却"""
        if service in self.active_connections:
            self.active_connections[service].append(connection)

# グローバル接続プール
connection_pool = ConnectionPool()

class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires']:
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """キャッシュに値を設定"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def delete(self, key: str):
        """キャッシュから値を削除"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """キャッシュをクリア"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """期限切れのキャッシュをクリーンアップ"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires']
        ]
        for key in expired_keys:
            del self.cache[key]

# グローバルキャッシュマネージャー
cache_manager = CacheManager()

class MemoryOptimizer:
    """メモリ最適化クラス"""
    
    @staticmethod
    def optimize_memory():
        """メモリ最適化を実行"""
        # ガベージコレクションを強制実行
        collected = gc.collect()
        logger.info(f"Garbage collection collected {collected} objects")
        
        # メモリ使用量をログ出力
        process = psutil.Process()
        memory_info = process.memory_info()
        logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        
        return {
            "objects_collected": collected,
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent()
        }
    
    @staticmethod
    def get_memory_recommendations() -> List[str]:
        """メモリ最適化の推奨事項を取得"""
        recommendations = []
        process = psutil.Process()
        
        memory_percent = process.memory_percent()
        if memory_percent > 80:
            recommendations.append("メモリ使用量が80%を超えています。不要なオブジェクトの削除を検討してください。")
        
        if memory_percent > 90:
            recommendations.append("メモリ使用量が90%を超えています。緊急のメモリ最適化が必要です。")
        
        # オープンファイル数のチェック
        open_files = len(process.open_files())
        if open_files > 1000:
            recommendations.append(f"オープンファイル数が{open_files}個と多すぎます。ファイルハンドルのリークを確認してください。")
        
        return recommendations

# バックグラウンドタスク
async def background_optimization():
    """バックグラウンド最適化タスク"""
    while True:
        try:
            # メモリ最適化
            MemoryOptimizer.optimize_memory()
            
            # キャッシュクリーンアップ
            cache_manager.cleanup_expired()
            
            # 60秒間隔で実行
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Background optimization error: {e}")
            await asyncio.sleep(60)

def start_background_optimization():
    """バックグラウンド最適化を開始"""
    asyncio.create_task(background_optimization())
