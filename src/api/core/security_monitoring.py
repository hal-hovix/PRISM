#!/usr/bin/env python3
"""
PRISM Security Monitoring Module
セキュリティ監視・ログ機能
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """セキュリティイベントタイプ"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_REQUEST = "suspicious_request"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    API_KEY_MISUSE = "api_key_misuse"
    FILE_UPLOAD_ABUSE = "file_upload_abuse"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"

class SecurityLevel(Enum):
    """セキュリティレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """セキュリティイベント"""
    event_type: SecurityEventType
    level: SecurityLevel
    client_id: str
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: int = 0

@dataclass
class SecurityAlert:
    """セキュリティアラート"""
    alert_id: str
    event_type: SecurityEventType
    level: SecurityLevel
    client_id: str
    ip_address: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)

class SecurityMonitor:
    """セキュリティ監視器"""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # 最新10000件のイベント
        self.alerts: List[SecurityAlert] = []
        self.client_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "failed_requests": 0,
            "suspicious_requests": 0,
            "last_request": None,
            "risk_score": 0,
            "blocked": False,
            "blocked_until": None
        })
        self.ip_blacklist: set = set()
        self.ip_whitelist: set = set()
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
        
    def log_event(self, event: SecurityEvent):
        """セキュリティイベントをログ"""
        self.events.append(event)
        
        # クライアント統計を更新
        client_id = event.client_id
        stats = self.client_stats[client_id]
        stats["total_requests"] += 1
        stats["last_request"] = event.timestamp
        
        if event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            stats["suspicious_requests"] += 1
        
        # リスクスコアを計算
        self._update_risk_score(client_id, event)
        
        # アラート生成をチェック
        self._check_for_alerts(event)
        
        # ログ出力
        self._log_security_event(event)
    
    def _update_risk_score(self, client_id: str, event: SecurityEvent):
        """リスクスコアを更新"""
        stats = self.client_stats[client_id]
        
        # イベントタイプに応じたスコア加算
        score_map = {
            SecurityEventType.LOGIN_FAILURE: 5,
            SecurityEventType.RATE_LIMIT_EXCEEDED: 3,
            SecurityEventType.SUSPICIOUS_REQUEST: 10,
            SecurityEventType.SQL_INJECTION_ATTEMPT: 50,
            SecurityEventType.XSS_ATTEMPT: 50,
            SecurityEventType.UNAUTHORIZED_ACCESS: 20,
            SecurityEventType.API_KEY_MISUSE: 15,
            SecurityEventType.FILE_UPLOAD_ABUSE: 25,
            SecurityEventType.BRUTE_FORCE_ATTEMPT: 30,
        }
        
        score_increase = score_map.get(event.event_type, 1)
        stats["risk_score"] += score_increase
        
        # 時間経過によるスコア減衰（1時間で10%減衰）
        time_since_last = (datetime.now() - stats["last_request"]).total_seconds()
        if time_since_last > 3600:  # 1時間
            decay_factor = 0.9
            stats["risk_score"] = int(stats["risk_score"] * decay_factor)
        
        # リスクスコアが閾値を超えた場合の処理
        if stats["risk_score"] > 100:
            self._block_client(client_id, duration_minutes=60)
        elif stats["risk_score"] > 50:
            self._block_client(client_id, duration_minutes=15)
    
    def _check_for_alerts(self, event: SecurityEvent):
        """アラート生成をチェック"""
        # 重大なイベントの場合は即座にアラート
        if event.level == SecurityLevel.CRITICAL:
            self._create_alert(event, "Critical security event detected")
        
        # 連続した失敗ログイン
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            recent_failures = [
                e for e in self.events
                if e.event_type == SecurityEventType.LOGIN_FAILURE
                and e.client_id == event.client_id
                and (datetime.now() - e.timestamp).total_seconds() < 300  # 5分以内
            ]
            if len(recent_failures) >= 5:
                self._create_alert(event, f"Multiple login failures detected ({len(recent_failures)} attempts)")
        
        # 疑わしいリクエストパターン
        if event.event_type == SecurityEventType.SUSPICIOUS_REQUEST:
            pattern_key = f"{event.client_id}:{event.endpoint}"
            self.suspicious_patterns[pattern_key] += 1
            
            if self.suspicious_patterns[pattern_key] >= 10:
                self._create_alert(event, f"Suspicious request pattern detected ({self.suspicious_patterns[pattern_key]} occurrences)")
    
    def _create_alert(self, event: SecurityEvent, message: str):
        """セキュリティアラートを作成"""
        alert_id = hashlib.md5(f"{event.client_id}:{event.timestamp.isoformat()}".encode()).hexdigest()[:16]
        
        alert = SecurityAlert(
            alert_id=alert_id,
            event_type=event.event_type,
            level=event.level,
            client_id=event.client_id,
            ip_address=event.ip_address,
            message=message,
            timestamp=datetime.now(),
            details=event.details
        )
        
        self.alerts.append(alert)
        
        # アラートをログ出力
        logger.critical(f"SECURITY ALERT: {message} - Client: {event.client_id}, IP: {event.ip_address}")
    
    def _block_client(self, client_id: str, duration_minutes: int = 15):
        """クライアントをブロック"""
        stats = self.client_stats[client_id]
        stats["blocked"] = True
        stats["blocked_until"] = datetime.now() + timedelta(minutes=duration_minutes)
        
        logger.warning(f"Client {client_id} blocked for {duration_minutes} minutes")
    
    def _log_security_event(self, event: SecurityEvent):
        """セキュリティイベントをログ出力"""
        log_data = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "level": event.level.value,
            "client_id": event.client_id,
            "ip_address": event.ip_address,
            "endpoint": event.endpoint,
            "method": event.method,
            "risk_score": event.risk_score,
            "details": event.details
        }
        
        if event.level == SecurityLevel.CRITICAL:
            logger.critical(f"SECURITY EVENT: {json.dumps(log_data)}")
        elif event.level == SecurityLevel.HIGH:
            logger.error(f"SECURITY EVENT: {json.dumps(log_data)}")
        elif event.level == SecurityLevel.MEDIUM:
            logger.warning(f"SECURITY EVENT: {json.dumps(log_data)}")
        else:
            logger.info(f"SECURITY EVENT: {json.dumps(log_data)}")
    
    def is_client_blocked(self, client_id: str) -> bool:
        """クライアントがブロックされているかチェック"""
        if client_id not in self.client_stats:
            return False
        
        stats = self.client_stats[client_id]
        
        if not stats["blocked"]:
            return False
        
        if stats["blocked_until"] and datetime.now() >= stats["blocked_until"]:
            # ブロック期間が終了
            stats["blocked"] = False
            stats["blocked_until"] = None
            return False
        
        return True
    
    def get_client_risk_score(self, client_id: str) -> int:
        """クライアントのリスクスコアを取得"""
        return self.client_stats.get(client_id, {}).get("risk_score", 0)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """セキュリティサマリーを取得"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_events = [e for e in self.events if e.timestamp >= last_hour]
        daily_events = [e for e in self.events if e.timestamp >= last_day]
        
        # イベントタイプ別集計
        event_counts = defaultdict(int)
        for event in daily_events:
            event_counts[event.event_type.value] += 1
        
        # レベル別集計
        level_counts = defaultdict(int)
        for event in daily_events:
            level_counts[event.level.value] += 1
        
        # アクティブなアラート
        active_alerts = [a for a in self.alerts if not a.resolved]
        
        # ブロックされたクライアント
        blocked_clients = [
            client_id for client_id, stats in self.client_stats.items()
            if stats["blocked"]
        ]
        
        return {
            "summary": {
                "total_events_today": len(daily_events),
                "events_last_hour": len(recent_events),
                "active_alerts": len(active_alerts),
                "blocked_clients": len(blocked_clients),
                "total_clients": len(self.client_stats)
            },
            "event_breakdown": dict(event_counts),
            "level_breakdown": dict(level_counts),
            "top_risky_clients": sorted(
                [(client_id, stats["risk_score"]) for client_id, stats in self.client_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "recent_alerts": [
                {
                    "alert_id": a.alert_id,
                    "level": a.level.value,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                    "client_id": a.client_id
                }
                for a in active_alerts[-10:]  # 最新10件
            ]
        }
    
    def resolve_alert(self, alert_id: str):
        """アラートを解決"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Security alert {alert_id} resolved")
                break
    
    def add_to_blacklist(self, ip_address: str):
        """IPアドレスをブラックリストに追加"""
        self.ip_blacklist.add(ip_address)
        logger.warning(f"IP address {ip_address} added to blacklist")
    
    def add_to_whitelist(self, ip_address: str):
        """IPアドレスをホワイトリストに追加"""
        self.ip_whitelist.add(ip_address)
        logger.info(f"IP address {ip_address} added to whitelist")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """IPアドレスがブロックされているかチェック"""
        return ip_address in self.ip_blacklist
    
    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """IPアドレスがホワイトリストに登録されているかチェック"""
        return ip_address in self.ip_whitelist

# グローバルセキュリティ監視器
security_monitor = SecurityMonitor()

def log_security_event(
    event_type: SecurityEventType,
    level: SecurityLevel,
    client_id: str,
    ip_address: str,
    user_agent: str,
    endpoint: str,
    method: str,
    details: Dict[str, Any] = None
):
    """セキュリティイベントをログ"""
    event = SecurityEvent(
        event_type=event_type,
        level=level,
        client_id=client_id,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        timestamp=datetime.now(),
        details=details or {}
    )
    
    security_monitor.log_event(event)
