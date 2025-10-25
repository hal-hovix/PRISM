#!/usr/bin/env python3
"""
PRISM Notification Escalation System
通知エスカレーション - 段階的な通知強化システム
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
from threading import Lock
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EscalationLevel(Enum):
    """エスカレーションレベル"""
    LEVEL_1 = 1  # 初期通知
    LEVEL_2 = 2  # 第1回エスカレーション
    LEVEL_3 = 3  # 第2回エスカレーション
    LEVEL_4 = 4  # 最終エスカレーション

class EscalationTrigger(Enum):
    """エスカレーショントリガー"""
    NO_RESPONSE = "no_response"
    NO_ACKNOWLEDGMENT = "no_acknowledgment"
    CRITICAL_PRIORITY = "critical_priority"
    TIME_BASED = "time_based"
    FAILURE_COUNT = "failure_count"

class EscalationAction(Enum):
    """エスカレーションアクション"""
    SEND_NOTIFICATION = "send_notification"
    ADD_CHANNELS = "add_channels"
    INCREASE_FREQUENCY = "increase_frequency"
    CHANGE_PRIORITY = "change_priority"
    NOTIFY_MANAGER = "notify_manager"
    CREATE_TICKET = "create_ticket"

@dataclass
class EscalationRule:
    """エスカレーションルール"""
    id: str
    name: str
    notification_type: str
    trigger: EscalationTrigger
    trigger_conditions: Dict[str, Any]
    escalation_level: EscalationLevel
    delay_minutes: int = 0
    actions: List[EscalationAction] = field(default_factory=list)
    action_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class EscalationContext:
    """エスカレーションコンテキスト"""
    notification_id: str
    notification_type: str
    priority: str
    urgency: str
    user_id: str
    created_at: datetime
    last_sent_at: Optional[datetime] = None
    acknowledgment_received: bool = False
    response_received: bool = False
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EscalationEvent:
    """エスカレーションイベント"""
    id: str
    notification_id: str
    escalation_level: EscalationLevel
    trigger: EscalationTrigger
    actions_taken: List[EscalationAction]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class NotificationEscalationManager:
    """通知エスカレーション管理"""
    
    def __init__(self):
        self.escalation_rules: Dict[str, EscalationRule] = {}
        self.active_contexts: Dict[str, EscalationContext] = {}
        self.escalation_history: List[EscalationEvent] = []
        self.lock = Lock()
        
        # デフォルトルールの初期化
        self._initialize_default_rules()
        
        logger.info("NotificationEscalationManager initialized")
    
    def _initialize_default_rules(self):
        """デフォルトエスカレーションルールの初期化"""
        default_rules = [
            # クリティカル優先度の即座エスカレーション
            EscalationRule(
                id="critical_immediate",
                name="クリティカル即座エスカレーション",
                notification_type="system_alert",
                trigger=EscalationTrigger.CRITICAL_PRIORITY,
                trigger_conditions={"priority": "critical"},
                escalation_level=EscalationLevel.LEVEL_2,
                delay_minutes=0,
                actions=[EscalationAction.ADD_CHANNELS, EscalationAction.INCREASE_FREQUENCY],
                action_config={
                    "additional_channels": ["sms", "webhook"],
                    "frequency_multiplier": 2
                }
            ),
            
            # タスクリマインダーの時間ベースエスカレーション
            EscalationRule(
                id="task_reminder_time",
                name="タスクリマインダー時間エスカレーション",
                notification_type="task_reminder",
                trigger=EscalationTrigger.TIME_BASED,
                trigger_conditions={"delay_minutes": 60},
                escalation_level=EscalationLevel.LEVEL_2,
                delay_minutes=60,
                actions=[EscalationAction.CHANGE_PRIORITY, EscalationAction.ADD_CHANNELS],
                action_config={
                    "new_priority": "high",
                    "additional_channels": ["email"]
                }
            ),
            
            # システムアラートの応答なしエスカレーション
            EscalationRule(
                id="system_alert_no_response",
                name="システムアラート応答なしエスカレーション",
                notification_type="system_alert",
                trigger=EscalationTrigger.NO_RESPONSE,
                trigger_conditions={"response_timeout_minutes": 30},
                escalation_level=EscalationLevel.LEVEL_3,
                delay_minutes=30,
                actions=[EscalationAction.NOTIFY_MANAGER, EscalationAction.CREATE_TICKET],
                action_config={
                    "manager_channels": ["email", "slack"],
                    "ticket_system": "jira"
                }
            ),
            
            # 高優先度通知の失敗エスカレーション
            EscalationRule(
                id="high_priority_failure",
                name="高優先度失敗エスカレーション",
                notification_type="*",
                trigger=EscalationTrigger.FAILURE_COUNT,
                trigger_conditions={"failure_threshold": 2},
                escalation_level=EscalationLevel.LEVEL_2,
                delay_minutes=5,
                actions=[EscalationAction.ADD_CHANNELS, EscalationAction.CHANGE_PRIORITY],
                action_config={
                    "additional_channels": ["sms", "webhook"],
                    "new_priority": "critical"
                }
            )
        ]
        
        for rule in default_rules:
            self.escalation_rules[rule.id] = rule
    
    def add_escalation_rule(self, rule: EscalationRule):
        """エスカレーションルールを追加"""
        with self.lock:
            self.escalation_rules[rule.id] = rule
            logger.info(f"Added escalation rule: {rule.name}")
    
    def update_escalation_rule(self, rule_id: str, updates: Dict[str, Any]):
        """エスカレーションルールを更新"""
        with self.lock:
            if rule_id in self.escalation_rules:
                rule = self.escalation_rules[rule_id]
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"Updated escalation rule: {rule_id}")
            else:
                logger.warning(f"Escalation rule not found: {rule_id}")
    
    def remove_escalation_rule(self, rule_id: str):
        """エスカレーションルールを削除"""
        with self.lock:
            if rule_id in self.escalation_rules:
                del self.escalation_rules[rule_id]
                logger.info(f"Removed escalation rule: {rule_id}")
            else:
                logger.warning(f"Escalation rule not found: {rule_id}")
    
    def start_escalation_context(self, context: EscalationContext):
        """エスカレーションコンテキストを開始"""
        with self.lock:
            self.active_contexts[context.notification_id] = context
            logger.info(f"Started escalation context for notification: {context.notification_id}")
    
    def update_escalation_context(self, notification_id: str, updates: Dict[str, Any]):
        """エスカレーションコンテキストを更新"""
        with self.lock:
            if notification_id in self.active_contexts:
                context = self.active_contexts[notification_id]
                for key, value in updates.items():
                    if hasattr(context, key):
                        setattr(context, key, value)
                logger.info(f"Updated escalation context: {notification_id}")
            else:
                logger.warning(f"Escalation context not found: {notification_id}")
    
    def end_escalation_context(self, notification_id: str, reason: str = "completed"):
        """エスカレーションコンテキストを終了"""
        with self.lock:
            if notification_id in self.active_contexts:
                context = self.active_contexts[notification_id]
                
                # 終了イベントを記録
                end_event = EscalationEvent(
                    id=f"end_{notification_id}_{int(time.time())}",
                    notification_id=notification_id,
                    escalation_level=context.escalation_level,
                    trigger=EscalationTrigger.NO_RESPONSE,  # ダミー
                    actions_taken=[],
                    timestamp=datetime.now(),
                    success=True,
                    metadata={"reason": reason}
                )
                
                self.escalation_history.append(end_event)
                del self.active_contexts[notification_id]
                
                logger.info(f"Ended escalation context: {notification_id}, reason: {reason}")
            else:
                logger.warning(f"Escalation context not found: {notification_id}")
    
    def check_escalation_triggers(self) -> List[Tuple[str, EscalationRule]]:
        """エスカレーショントリガーをチェック"""
        triggered_escalations = []
        
        with self.lock:
            for notification_id, context in self.active_contexts.items():
                applicable_rules = self._find_applicable_rules(context)
                
                for rule in applicable_rules:
                    if self._check_trigger_conditions(context, rule):
                        triggered_escalations.append((notification_id, rule))
        
        return triggered_escalations
    
    def _find_applicable_rules(self, context: EscalationContext) -> List[EscalationRule]:
        """適用可能なルールを検索"""
        applicable = []
        
        for rule in self.escalation_rules.values():
            if not rule.enabled:
                continue
            
            # 通知タイプのマッチング
            if rule.notification_type != "*" and rule.notification_type != context.notification_type:
                continue
            
            # エスカレーションレベルのチェック
            if rule.escalation_level <= context.escalation_level:
                continue
            
            applicable.append(rule)
        
        return applicable
    
    def _check_trigger_conditions(self, context: EscalationContext, rule: EscalationRule) -> bool:
        """トリガー条件をチェック"""
        conditions = rule.trigger_conditions
        
        if rule.trigger == EscalationTrigger.CRITICAL_PRIORITY:
            return context.priority == conditions.get("priority", "critical")
        
        elif rule.trigger == EscalationTrigger.TIME_BASED:
            if not context.last_sent_at:
                return False
            
            delay_minutes = conditions.get("delay_minutes", 0)
            time_threshold = context.last_sent_at + timedelta(minutes=delay_minutes)
            return datetime.now() >= time_threshold
        
        elif rule.trigger == EscalationTrigger.NO_RESPONSE:
            response_timeout = conditions.get("response_timeout_minutes", 30)
            time_threshold = context.created_at + timedelta(minutes=response_timeout)
            return datetime.now() >= time_threshold and not context.response_received
        
        elif rule.trigger == EscalationTrigger.NO_ACKNOWLEDGMENT:
            ack_timeout = conditions.get("acknowledgment_timeout_minutes", 15)
            time_threshold = context.created_at + timedelta(minutes=ack_timeout)
            return datetime.now() >= time_threshold and not context.acknowledgment_received
        
        elif rule.trigger == EscalationTrigger.FAILURE_COUNT:
            failure_threshold = conditions.get("failure_threshold", 2)
            failure_count = len([h for h in context.escalation_history if not h.get("success", True)])
            return failure_count >= failure_threshold
        
        return False
    
    async def execute_escalation(self, notification_id: str, rule: EscalationRule) -> EscalationEvent:
        """エスカレーションを実行"""
        logger.info(f"Executing escalation for notification {notification_id} with rule {rule.name}")
        
        context = self.active_contexts.get(notification_id)
        if not context:
            raise ValueError(f"Escalation context not found: {notification_id}")
        
        # エスカレーションイベント作成
        event = EscalationEvent(
            id=f"escalation_{notification_id}_{int(time.time())}",
            notification_id=notification_id,
            escalation_level=rule.escalation_level,
            trigger=rule.trigger,
            actions_taken=rule.actions,
            timestamp=datetime.now(),
            success=False
        )
        
        try:
            # エスカレーションアクションの実行
            for action in rule.actions:
                await self._execute_escalation_action(context, action, rule.action_config)
            
            # コンテキストの更新
            context.escalation_level = rule.escalation_level
            context.escalation_history.append({
                "level": rule.escalation_level.value,
                "rule_id": rule.id,
                "timestamp": datetime.now().isoformat(),
                "actions": [a.value for a in rule.actions],
                "success": True
            })
            
            event.success = True
            
        except Exception as e:
            logger.error(f"Escalation execution failed: {e}")
            event.error_message = str(e)
            
            context.escalation_history.append({
                "level": rule.escalation_level.value,
                "rule_id": rule.id,
                "timestamp": datetime.now().isoformat(),
                "actions": [a.value for a in rule.actions],
                "success": False,
                "error": str(e)
            })
        
        # イベント履歴に追加
        with self.lock:
            self.escalation_history.append(event)
        
        return event
    
    async def _execute_escalation_action(self, context: EscalationContext, 
                                       action: EscalationAction, config: Dict[str, Any]):
        """エスカレーションアクションを実行"""
        if action == EscalationAction.SEND_NOTIFICATION:
            await self._send_escalated_notification(context, config)
        
        elif action == EscalationAction.ADD_CHANNELS:
            await self._add_notification_channels(context, config)
        
        elif action == EscalationAction.INCREASE_FREQUENCY:
            await self._increase_notification_frequency(context, config)
        
        elif action == EscalationAction.CHANGE_PRIORITY:
            await self._change_notification_priority(context, config)
        
        elif action == EscalationAction.NOTIFY_MANAGER:
            await self._notify_manager(context, config)
        
        elif action == EscalationAction.CREATE_TICKET:
            await self._create_support_ticket(context, config)
    
    async def _send_escalated_notification(self, context: EscalationContext, config: Dict[str, Any]):
        """エスカレーション通知を送信"""
        # マルチチャンネル通知システムを使用
        from multi_channel_notifications import multi_channel_manager, NotificationRequest, ChannelType
        
        escalated_request = NotificationRequest(
            id=f"escalated_{context.notification_id}",
            title=f"[エスカレーション] {context.notification_id}",
            content=f"この通知はエスカレーションされました。レベル: {context.escalation_level.value}",
            priority=config.get("priority", "high"),
            urgency=config.get("urgency", "high"),
            channels=[ChannelType.SLACK, ChannelType.EMAIL],
            user_id=context.user_id,
            metadata=context.metadata
        )
        
        await multi_channel_manager.send_notification(escalated_request)
    
    async def _add_notification_channels(self, context: EscalationContext, config: Dict[str, Any]):
        """通知チャンネルを追加"""
        additional_channels = config.get("additional_channels", [])
        logger.info(f"Adding channels for escalation: {additional_channels}")
        
        # チャンネル追加の実装（実際のシステムでは通知設定を更新）
        context.metadata["escalated_channels"] = additional_channels
    
    async def _increase_notification_frequency(self, context: EscalationContext, config: Dict[str, Any]):
        """通知頻度を増加"""
        frequency_multiplier = config.get("frequency_multiplier", 2)
        logger.info(f"Increasing notification frequency by {frequency_multiplier}x")
        
        # 頻度増加の実装
        context.metadata["frequency_multiplier"] = frequency_multiplier
    
    async def _change_notification_priority(self, context: EscalationContext, config: Dict[str, Any]):
        """通知優先度を変更"""
        new_priority = config.get("new_priority", "high")
        logger.info(f"Changing notification priority to {new_priority}")
        
        context.priority = new_priority
    
    async def _notify_manager(self, context: EscalationContext, config: Dict[str, Any]):
        """管理者に通知"""
        manager_channels = config.get("manager_channels", ["email"])
        logger.info(f"Notifying manager via channels: {manager_channels}")
        
        # 管理者通知の実装
        context.metadata["manager_notified"] = True
        context.metadata["manager_channels"] = manager_channels
    
    async def _create_support_ticket(self, context: EscalationContext, config: Dict[str, Any]):
        """サポートチケットを作成"""
        ticket_system = config.get("ticket_system", "jira")
        logger.info(f"Creating support ticket in {ticket_system}")
        
        # チケット作成の実装
        context.metadata["support_ticket_created"] = True
        context.metadata["ticket_system"] = ticket_system
    
    def get_escalation_status(self) -> Dict[str, Any]:
        """エスカレーションステータスを取得"""
        with self.lock:
            active_count = len(self.active_contexts)
            total_rules = len(self.escalation_rules)
            enabled_rules = len([r for r in self.escalation_rules.values() if r.enabled])
            
            return {
                "active_contexts": active_count,
                "total_rules": total_rules,
                "enabled_rules": enabled_rules,
                "escalation_history_count": len(self.escalation_history),
                "recent_escalations": len([
                    e for e in self.escalation_history 
                    if e.timestamp >= datetime.now() - timedelta(hours=24)
                ])
            }
    
    def get_escalation_history(self, notification_id: str = None, 
                              hours: int = 24) -> List[Dict[str, Any]]:
        """エスカレーション履歴を取得"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_history = [
                e for e in self.escalation_history 
                if e.timestamp >= cutoff_time
            ]
            
            if notification_id:
                filtered_history = [
                    e for e in filtered_history 
                    if e.notification_id == notification_id
                ]
            
            return [
                {
                    "id": event.id,
                    "notification_id": event.notification_id,
                    "escalation_level": event.escalation_level.value,
                    "trigger": event.trigger.value,
                    "actions_taken": [a.value for a in event.actions_taken],
                    "timestamp": event.timestamp.isoformat(),
                    "success": event.success,
                    "error_message": event.error_message,
                    "metadata": event.metadata
                }
                for event in filtered_history
            ]
    
    async def run_escalation_monitor(self):
        """エスカレーションモニターを実行"""
        logger.info("Starting escalation monitor")
        
        while True:
            try:
                # トリガーチェック
                triggered_escalations = self.check_escalation_triggers()
                
                # エスカレーション実行
                for notification_id, rule in triggered_escalations:
                    await self.execute_escalation(notification_id, rule)
                
                # 古いコンテキストのクリーンアップ
                self._cleanup_old_contexts()
                
                # 1分待機
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Escalation monitor error: {e}")
                await asyncio.sleep(60)
    
    def _cleanup_old_contexts(self):
        """古いコンテキストをクリーンアップ"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_contexts = [
                notification_id for notification_id, context in self.active_contexts.items()
                if context.created_at < cutoff_time
            ]
            
            for notification_id in old_contexts:
                self.end_escalation_context(notification_id, "timeout")

# グローバルインスタンス
escalation_manager = NotificationEscalationManager()

def main():
    """テスト用メイン関数"""
    # テストエスカレーションコンテキスト
    test_context = EscalationContext(
        notification_id="test_notification_1",
        notification_type="system_alert",
        priority="critical",
        urgency="urgent",
        user_id="test_user",
        created_at=datetime.now()
    )
    
    escalation_manager.start_escalation_context(test_context)
    
    # エスカレーションステータス表示
    status = escalation_manager.get_escalation_status()
    print("Escalation Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
