#!/usr/bin/env python3
"""
PRISM Rate Limiting Module
レート制限機能
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """レート制限設定"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size: int = 60  # seconds

@dataclass
class RateLimitEntry:
    """レート制限エントリ"""
    requests: deque = field(default_factory=deque)
    last_reset: datetime = field(default_factory=datetime.now)
    blocked_until: Optional[datetime] = None
    violation_count: int = 0

class RateLimiter:
    """レート制限器"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.clients: Dict[str, RateLimitEntry] = {}
        self.global_requests: deque = deque()
        self.global_blocked_until: Optional[datetime] = None
        
    def _cleanup_old_requests(self, requests: deque, window_seconds: int):
        """古いリクエストをクリーンアップ"""
        current_time = time.time()
        while requests and current_time - requests[0] > window_seconds:
            requests.popleft()
    
    def _is_client_blocked(self, client_id: str) -> bool:
        """クライアントがブロックされているかチェック"""
        if client_id not in self.clients:
            return False
        
        entry = self.clients[client_id]
        if entry.blocked_until and datetime.now() < entry.blocked_until:
            return True
        
        # ブロック期間が終了したらリセット
        if entry.blocked_until and datetime.now() >= entry.blocked_until:
            entry.blocked_until = None
            entry.violation_count = 0
        
        return False
    
    def _block_client(self, client_id: str, duration_minutes: int = 5):
        """クライアントをブロック"""
        if client_id not in self.clients:
            self.clients[client_id] = RateLimitEntry()
        
        self.clients[client_id].blocked_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.clients[client_id].violation_count += 1
        
        logger.warning(f"Client {client_id} blocked for {duration_minutes} minutes (violation #{self.clients[client_id].violation_count})")
    
    def check_rate_limit(self, client_id: str, endpoint: str = "default") -> Tuple[bool, Dict[str, any]]:
        """レート制限をチェック"""
        current_time = time.time()
        
        # グローバルブロックチェック
        if self.global_blocked_until and datetime.now() < self.global_blocked_until:
            return False, {
                "error": "Global rate limit exceeded",
                "retry_after": int((self.global_blocked_until - datetime.now()).total_seconds()),
                "blocked_until": self.global_blocked_until.isoformat()
            }
        
        # クライアントブロックチェック
        if self._is_client_blocked(client_id):
            entry = self.clients[client_id]
            return False, {
                "error": "Client rate limit exceeded",
                "retry_after": int((entry.blocked_until - datetime.now()).total_seconds()),
                "blocked_until": entry.blocked_until.isoformat(),
                "violation_count": entry.violation_count
            }
        
        # クライアントエントリを初期化
        if client_id not in self.clients:
            self.clients[client_id] = RateLimitEntry()
        
        entry = self.clients[client_id]
        
        # 古いリクエストをクリーンアップ
        self._cleanup_old_requests(entry.requests, self.config.window_size)
        self._cleanup_old_requests(self.global_requests, self.config.window_size)
        
        # レート制限チェック
        if len(entry.requests) >= self.config.requests_per_minute:
            # 違反回数に応じてブロック期間を延長
            block_duration = min(5 * (entry.violation_count + 1), 60)  # 最大60分
            self._block_client(client_id, block_duration)
            return False, {
                "error": "Rate limit exceeded",
                "limit": self.config.requests_per_minute,
                "current": len(entry.requests),
                "retry_after": block_duration * 60,
                "violation_count": entry.violation_count + 1
            }
        
        # バースト制限チェック
        recent_requests = [req for req in entry.requests if current_time - req < 10]  # 過去10秒
        if len(recent_requests) >= self.config.burst_limit:
            self._block_client(client_id, 1)  # 1分間ブロック
            return False, {
                "error": "Burst limit exceeded",
                "limit": self.config.burst_limit,
                "current": len(recent_requests),
                "retry_after": 60
            }
        
        # グローバル制限チェック
        if len(self.global_requests) >= self.config.requests_per_minute * 10:  # 10倍のグローバル制限
            self.global_blocked_until = datetime.now() + timedelta(minutes=5)
            return False, {
                "error": "Global rate limit exceeded",
                "retry_after": 300
            }
        
        # リクエストを記録
        entry.requests.append(current_time)
        self.global_requests.append(current_time)
        
        return True, {
            "allowed": True,
            "remaining": self.config.requests_per_minute - len(entry.requests),
            "reset_time": int(current_time + self.config.window_size),
            "burst_remaining": self.config.burst_limit - len(recent_requests)
        }
    
    def get_client_stats(self, client_id: str) -> Dict[str, any]:
        """クライアント統計を取得"""
        if client_id not in self.clients:
            return {"error": "Client not found"}
        
        entry = self.clients[client_id]
        current_time = time.time()
        
        # 古いリクエストをクリーンアップ
        self._cleanup_old_requests(entry.requests, self.config.window_size)
        
        recent_requests = [req for req in entry.requests if current_time - req < 10]
        
        return {
            "client_id": client_id,
            "total_requests": len(entry.requests),
            "recent_requests": len(recent_requests),
            "violation_count": entry.violation_count,
            "is_blocked": self._is_client_blocked(client_id),
            "blocked_until": entry.blocked_until.isoformat() if entry.blocked_until else None,
            "last_reset": entry.last_reset.isoformat()
        }
    
    def reset_client(self, client_id: str):
        """クライアントをリセット"""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Client {client_id} rate limit reset")
    
    def get_global_stats(self) -> Dict[str, any]:
        """グローバル統計を取得"""
        current_time = time.time()
        self._cleanup_old_requests(self.global_requests, self.config.window_size)
        
        return {
            "total_clients": len(self.clients),
            "global_requests": len(self.global_requests),
            "is_globally_blocked": self.global_blocked_until and datetime.now() < self.global_blocked_until,
            "global_blocked_until": self.global_blocked_until.isoformat() if self.global_blocked_until else None,
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "burst_limit": self.config.burst_limit,
                "window_size": self.config.window_size
            }
        }

# グローバルレート制限器
rate_limiter = RateLimiter()

def get_client_id(request) -> str:
    """リクエストからクライアントIDを取得"""
    # IPアドレスをベースにしたクライアントID
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    
    # X-Forwarded-Forヘッダーがある場合はそれを使用
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # User-Agentも含めてより正確な識別
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # ハッシュ化してクライアントIDを生成
    import hashlib
    client_string = f"{client_ip}:{user_agent}"
    return hashlib.md5(client_string.encode()).hexdigest()[:16]
