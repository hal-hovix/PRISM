#!/usr/bin/env python3
"""
PRISM Smart Notification Filtering System
スマート通知フィルタリング - 重要度・緊急度ベースの通知制御
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
from threading import Lock

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Priority(Enum):
    """通知優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Urgency(Enum):
    """緊急度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationType(Enum):
    """通知タイプ"""
    TASK_REMINDER = "task_reminder"
    HABIT_NOTIFICATION = "habit_notification"
    SYSTEM_ALERT = "system_alert"
    DEADLINE_WARNING = "deadline_warning"
    PERFORMANCE_ALERT = "performance_alert"
    MAINTENANCE_NOTICE = "maintenance_notice"

@dataclass
class NotificationRule:
    """通知ルール"""
    id: str
    name: str
    notification_type: NotificationType
    priority_threshold: Priority
    urgency_threshold: Urgency
    time_restrictions: Dict[str, Any] = field(default_factory=dict)
    frequency_limits: Dict[str, int] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class NotificationContext:
    """通知コンテキスト"""
    notification_type: NotificationType
    priority: Priority
    urgency: Urgency
    user_id: str = "default"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationHistory:
    """通知履歴"""
    id: str
    notification_type: NotificationType
    priority: Priority
    urgency: Urgency
    sent_at: datetime
    channel: str
    success: bool
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class SmartNotificationFilter:
    """スマート通知フィルター"""
    
    def __init__(self):
        self.rules: Dict[str, NotificationRule] = {}
        self.history: List[NotificationHistory] = []
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.frequency_tracker: Dict[str, Dict[str, int]] = {}
        self.lock = Lock()
        
        # デフォルトルールの初期化
        self._initialize_default_rules()
        
        logger.info("SmartNotificationFilter initialized")
    
    def _initialize_default_rules(self):
        """デフォルトルールの初期化"""
        default_rules = [
            NotificationRule(
                id="task_reminder_high",
                name="高優先度タスクリマインダー",
                notification_type=NotificationType.TASK_REMINDER,
                priority_threshold=Priority.HIGH,
                urgency_threshold=Urgency.MEDIUM,
                time_restrictions={"start_hour": 8, "end_hour": 22},
                frequency_limits={"max_per_hour": 3, "max_per_day": 10}
            ),
            NotificationRule(
                id="system_alert_critical",
                name="クリティカルシステムアラート",
                notification_type=NotificationType.SYSTEM_ALERT,
                priority_threshold=Priority.CRITICAL,
                urgency_threshold=Urgency.URGENT,
                frequency_limits={"max_per_hour": 5, "max_per_day": 20}
            ),
            NotificationRule(
                id="deadline_warning",
                name="期日警告",
                notification_type=NotificationType.DEADLINE_WARNING,
                priority_threshold=Priority.MEDIUM,
                urgency_threshold=Urgency.HIGH,
                time_restrictions={"start_hour": 9, "end_hour": 18},
                frequency_limits={"max_per_hour": 2, "max_per_day": 5}
            ),
            NotificationRule(
                id="habit_notification_low",
                name="習慣通知（低優先度）",
                notification_type=NotificationType.HABIT_NOTIFICATION,
                priority_threshold=Priority.LOW,
                urgency_threshold=Urgency.LOW,
                time_restrictions={"start_hour": 20, "end_hour": 21},
                frequency_limits={"max_per_hour": 1, "max_per_day": 3}
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.id] = rule
    
    def add_rule(self, rule: NotificationRule):
        """ルールを追加"""
        with self.lock:
            self.rules[rule.id] = rule
            logger.info(f"Added notification rule: {rule.name}")
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]):
        """ルールを更新"""
        with self.lock:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"Updated notification rule: {rule_id}")
            else:
                logger.warning(f"Rule not found: {rule_id}")
    
    def remove_rule(self, rule_id: str):
        """ルールを削除"""
        with self.lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed notification rule: {rule_id}")
            else:
                logger.warning(f"Rule not found: {rule_id}")
    
    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """ユーザー設定を更新"""
        with self.lock:
            self.user_preferences[user_id] = preferences
            logger.info(f"Updated user preferences for: {user_id}")
    
    def should_send_notification(self, context: NotificationContext) -> Tuple[bool, str]:
        """通知を送信すべきか判定"""
        with self.lock:
            # 該当するルールを検索
            applicable_rules = self._find_applicable_rules(context)
            
            if not applicable_rules:
                return False, "No applicable rules found"
            
            # 最も厳しいルールを適用
            strictest_rule = min(applicable_rules, key=lambda r: (
                self._priority_value(r.priority_threshold),
                self._urgency_value(r.urgency_threshold)
            ))
            
            # 優先度・緊急度チェック
            if not self._meets_priority_threshold(context.priority, strictest_rule.priority_threshold):
                return False, f"Priority {context.priority.value} below threshold {strictest_rule.priority_threshold.value}"
            
            if not self._meets_urgency_threshold(context.urgency, strictest_rule.urgency_threshold):
                return False, f"Urgency {context.urgency.value} below threshold {strictest_rule.urgency_threshold.value}"
            
            # 時間制限チェック
            if not self._check_time_restrictions(strictest_rule.time_restrictions):
                return False, "Outside allowed time window"
            
            # 頻度制限チェック
            if not self._check_frequency_limits(context, strictest_rule):
                return False, "Frequency limit exceeded"
            
            # ユーザー設定チェック
            if not self._check_user_preferences(context, strictest_rule):
                return False, "Blocked by user preferences"
            
            return True, "Notification approved"
    
    def _find_applicable_rules(self, context: NotificationContext) -> List[NotificationRule]:
        """該当するルールを検索"""
        applicable = []
        for rule in self.rules.values():
            if (rule.enabled and 
                rule.notification_type == context.notification_type):
                applicable.append(rule)
        return applicable
    
    def _priority_value(self, priority: Priority) -> int:
        """優先度の数値化"""
        priority_values = {
            Priority.LOW: 1,
            Priority.MEDIUM: 2,
            Priority.HIGH: 3,
            Priority.CRITICAL: 4
        }
        return priority_values.get(priority, 0)
    
    def _urgency_value(self, urgency: Urgency) -> int:
        """緊急度の数値化"""
        urgency_values = {
            Urgency.LOW: 1,
            Urgency.MEDIUM: 2,
            Urgency.HIGH: 3,
            Urgency.URGENT: 4
        }
        return urgency_values.get(urgency, 0)
    
    def _meets_priority_threshold(self, priority: Priority, threshold: Priority) -> bool:
        """優先度閾値チェック"""
        return self._priority_value(priority) >= self._priority_value(threshold)
    
    def _meets_urgency_threshold(self, urgency: Urgency, threshold: Urgency) -> bool:
        """緊急度閾値チェック"""
        return self._urgency_value(urgency) >= self._urgency_value(threshold)
    
    def _check_time_restrictions(self, restrictions: Dict[str, Any]) -> bool:
        """時間制限チェック"""
        if not restrictions:
            return True
        
        now = datetime.now()
        current_hour = now.hour
        
        start_hour = restrictions.get("start_hour", 0)
        end_hour = restrictions.get("end_hour", 23)
        
        return start_hour <= current_hour <= end_hour
    
    def _check_frequency_limits(self, context: NotificationContext, rule: NotificationRule) -> bool:
        """頻度制限チェック"""
        limits = rule.frequency_limits
        if not limits:
            return True
        
        user_id = context.user_id
        notification_type = context.notification_type.value
        
        # 頻度トラッカーの初期化
        if user_id not in self.frequency_tracker:
            self.frequency_tracker[user_id] = {}
        
        if notification_type not in self.frequency_tracker[user_id]:
            self.frequency_tracker[user_id][notification_type] = {
                "hourly": 0,
                "daily": 0,
                "last_hour_reset": datetime.now().replace(minute=0, second=0, microsecond=0),
                "last_day_reset": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            }
        
        tracker = self.frequency_tracker[user_id][notification_type]
        now = datetime.now()
        
        # 時間リセットチェック
        if now >= tracker["last_hour_reset"] + timedelta(hours=1):
            tracker["hourly"] = 0
            tracker["last_hour_reset"] = now.replace(minute=0, second=0, microsecond=0)
        
        if now >= tracker["last_day_reset"] + timedelta(days=1):
            tracker["daily"] = 0
            tracker["last_day_reset"] = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 制限チェック
        max_per_hour = limits.get("max_per_hour", float('inf'))
        max_per_day = limits.get("max_per_day", float('inf'))
        
        if tracker["hourly"] >= max_per_hour:
            return False
        
        if tracker["daily"] >= max_per_day:
            return False
        
        # カウンター更新
        tracker["hourly"] += 1
        tracker["daily"] += 1
        
        return True
    
    def _check_user_preferences(self, context: NotificationContext, rule: NotificationRule) -> bool:
        """ユーザー設定チェック"""
        user_id = context.user_id
        if user_id not in self.user_preferences:
            return True
        
        preferences = self.user_preferences[user_id]
        
        # 通知タイプ別の設定チェック
        notification_type = context.notification_type.value
        if notification_type in preferences.get("disabled_types", []):
            return False
        
        # 優先度別の設定チェック
        priority = context.priority.value
        if priority in preferences.get("disabled_priorities", []):
            return False
        
        # 時間帯設定チェック
        quiet_hours = preferences.get("quiet_hours", {})
        if quiet_hours:
            now = datetime.now()
            current_hour = now.hour
            
            start_hour = quiet_hours.get("start", 22)
            end_hour = quiet_hours.get("end", 8)
            
            if start_hour > end_hour:  # 夜間（例：22:00-08:00）
                if current_hour >= start_hour or current_hour <= end_hour:
                    # 緊急度が高い場合は例外
                    if context.urgency != Urgency.URGENT and context.priority != Priority.CRITICAL:
                        return False
            else:  # 日中の時間帯
                if start_hour <= current_hour <= end_hour:
                    if context.urgency != Urgency.URGENT and context.priority != Priority.CRITICAL:
                        return False
        
        return True
    
    def record_notification(self, history: NotificationHistory):
        """通知履歴を記録"""
        with self.lock:
            self.history.append(history)
            
            # 履歴の保持期間制限（過去30日）
            cutoff_date = datetime.now() - timedelta(days=30)
            self.history = [h for h in self.history if h.sent_at >= cutoff_date]
            
            logger.info(f"Recorded notification: {history.notification_type.value}")
    
    def get_notification_stats(self, user_id: str = None, days: int = 7) -> Dict[str, Any]:
        """通知統計を取得"""
        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_history = [h for h in self.history if h.sent_at >= cutoff_date]
            
            if user_id:
                filtered_history = [h for h in filtered_history if h.user_id == user_id]
            
            stats = {
                "total_notifications": len(filtered_history),
                "successful_notifications": len([h for h in filtered_history if h.success]),
                "failed_notifications": len([h for h in filtered_history if not h.success]),
                "by_type": {},
                "by_priority": {},
                "by_channel": {},
                "daily_counts": {}
            }
            
            # タイプ別統計
            for notification_type in NotificationType:
                count = len([h for h in filtered_history if h.notification_type == notification_type])
                stats["by_type"][notification_type.value] = count
            
            # 優先度別統計
            for priority in Priority:
                count = len([h for h in filtered_history if h.priority == priority])
                stats["by_priority"][priority.value] = count
            
            # チャンネル別統計
            channels = set(h.channel for h in filtered_history)
            for channel in channels:
                count = len([h for h in filtered_history if h.channel == channel])
                stats["by_channel"][channel] = count
            
            # 日別統計
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).date()
                count = len([h for h in filtered_history if h.sent_at.date() == date])
                stats["daily_counts"][date.isoformat()] = count
            
            return stats
    
    def get_filtered_rules(self) -> List[Dict[str, Any]]:
        """フィルタリングルール一覧を取得"""
        with self.lock:
            return [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "notification_type": rule.notification_type.value,
                    "priority_threshold": rule.priority_threshold.value,
                    "urgency_threshold": rule.urgency_threshold.value,
                    "time_restrictions": rule.time_restrictions,
                    "frequency_limits": rule.frequency_limits,
                    "enabled": rule.enabled
                }
                for rule in self.rules.values()
            ]

# グローバルインスタンス
smart_filter = SmartNotificationFilter()

def main():
    """テスト用メイン関数"""
    # テスト通知コンテキスト
    context = NotificationContext(
        notification_type=NotificationType.TASK_REMINDER,
        priority=Priority.HIGH,
        urgency=Urgency.MEDIUM,
        user_id="test_user"
    )
    
    should_send, reason = smart_filter.should_send_notification(context)
    print(f"Should send notification: {should_send}, Reason: {reason}")
    
    # 統計情報の表示
    stats = smart_filter.get_notification_stats()
    print(f"Notification stats: {stats}")

if __name__ == "__main__":
    main()
