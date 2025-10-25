#!/usr/bin/env python3
"""
PRISM Notification Analytics System
通知履歴・分析機能 - 通知効果の追跡と分析
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
import asyncio
import aiohttp
from threading import Lock
import statistics
from collections import defaultdict, Counter

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationStatus(Enum):
    """通知ステータス"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"

class ChannelType(Enum):
    """通知チャンネルタイプ"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"

@dataclass
class NotificationEvent:
    """通知イベント"""
    id: str
    notification_id: str
    event_type: NotificationStatus
    timestamp: datetime
    channel: ChannelType
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationMetrics:
    """通知メトリクス"""
    total_sent: int = 0
    total_delivered: int = 0
    total_read: int = 0
    total_clicked: int = 0
    total_failed: int = 0
    delivery_rate: float = 0.0
    read_rate: float = 0.0
    click_rate: float = 0.0
    failure_rate: float = 0.0
    avg_delivery_time: float = 0.0
    avg_read_time: float = 0.0

@dataclass
class UserEngagement:
    """ユーザーエンゲージメント"""
    user_id: str
    total_notifications: int = 0
    read_notifications: int = 0
    clicked_notifications: int = 0
    engagement_rate: float = 0.0
    preferred_channels: List[str] = field(default_factory=list)
    response_time_avg: float = 0.0
    last_activity: Optional[datetime] = None

class NotificationAnalytics:
    """通知分析システム"""
    
    def __init__(self, db_path: str = "/tmp/notification_analytics.db"):
        self.db_path = db_path
        self.lock = Lock()
        
        # データベース初期化
        self._initialize_database()
        
        logger.info("NotificationAnalytics initialized")
    
    def _initialize_database(self):
        """データベース初期化"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 通知イベントテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_events (
                    id TEXT PRIMARY KEY,
                    notification_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 通知統計テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_stats (
                    id TEXT PRIMARY KEY,
                    notification_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    delivered_at TEXT,
                    read_at TEXT,
                    clicked_at TEXT,
                    failed_at TEXT,
                    delivery_time_ms INTEGER,
                    read_time_ms INTEGER,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # インデックス作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_id ON notification_events(notification_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON notification_events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON notification_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channel ON notification_events(channel)')
            
            conn.commit()
            conn.close()
    
    def record_event(self, event: NotificationEvent):
        """イベントを記録"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO notification_events 
                (id, notification_id, event_type, timestamp, channel, user_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.id,
                event.notification_id,
                event.event_type.value,
                event.timestamp.isoformat(),
                event.channel.value,
                event.user_id,
                json.dumps(event.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded event: {event.event_type.value} for notification {event.notification_id}")
    
    def record_notification_stats(self, stats_data: Dict[str, Any]):
        """通知統計を記録"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO notification_stats 
                (id, notification_id, notification_type, priority, urgency, channel, user_id,
                 sent_at, delivered_at, read_at, clicked_at, failed_at, 
                 delivery_time_ms, read_time_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stats_data.get('id'),
                stats_data.get('notification_id'),
                stats_data.get('notification_type'),
                stats_data.get('priority'),
                stats_data.get('urgency'),
                stats_data.get('channel'),
                stats_data.get('user_id'),
                stats_data.get('sent_at'),
                stats_data.get('delivered_at'),
                stats_data.get('read_at'),
                stats_data.get('clicked_at'),
                stats_data.get('failed_at'),
                stats_data.get('delivery_time_ms'),
                stats_data.get('read_time_ms'),
                json.dumps(stats_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
    
    def get_notification_metrics(self, 
                                user_id: str = None,
                                channel: ChannelType = None,
                                start_date: datetime = None,
                                end_date: datetime = None) -> NotificationMetrics:
        """通知メトリクスを取得"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基本クエリ
            query = '''
                SELECT event_type, COUNT(*) as count, AVG(CAST(metadata->>'delivery_time_ms' AS INTEGER)) as avg_delivery_time
                FROM notification_events
                WHERE 1=1
            '''
            params = []
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if channel:
                query += ' AND channel = ?'
                params.append(channel.value)
            
            if start_date:
                query += ' AND timestamp >= ?'
                params.append(start_date.isoformat())
            
            if end_date:
                query += ' AND timestamp <= ?'
                params.append(end_date.isoformat())
            
            query += ' GROUP BY event_type'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            conn.close()
            
            # メトリクス計算
            metrics = NotificationMetrics()
            event_counts = {}
            delivery_times = []
            
            for event_type, count, avg_delivery_time in results:
                event_counts[event_type] = count
                if avg_delivery_time:
                    delivery_times.append(avg_delivery_time)
            
            metrics.total_sent = event_counts.get('sent', 0)
            metrics.total_delivered = event_counts.get('delivered', 0)
            metrics.total_read = event_counts.get('read', 0)
            metrics.total_clicked = event_counts.get('clicked', 0)
            metrics.total_failed = event_counts.get('failed', 0)
            
            # レート計算
            if metrics.total_sent > 0:
                metrics.delivery_rate = (metrics.total_delivered / metrics.total_sent) * 100
                metrics.read_rate = (metrics.total_read / metrics.total_sent) * 100
                metrics.click_rate = (metrics.total_clicked / metrics.total_sent) * 100
                metrics.failure_rate = (metrics.total_failed / metrics.total_sent) * 100
            
            if delivery_times:
                metrics.avg_delivery_time = statistics.mean(delivery_times)
            
            return metrics
    
    def get_user_engagement(self, user_id: str, days: int = 30) -> UserEngagement:
        """ユーザーエンゲージメントを取得"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # ユーザーの通知統計
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read_count,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_count,
                    AVG(CASE WHEN read_at IS NOT NULL AND sent_at IS NOT NULL 
                        THEN (julianday(read_at) - julianday(sent_at)) * 24 * 60 * 60 * 1000 
                        END) as avg_response_time
                FROM notification_stats 
                WHERE user_id = ? AND sent_at >= ?
            ''', (user_id, start_date.isoformat()))
            
            total, read_count, clicked_count, avg_response_time = cursor.fetchone()
            
            # チャンネル別統計
            cursor.execute('''
                SELECT channel, COUNT(*) as count
                FROM notification_stats 
                WHERE user_id = ? AND sent_at >= ?
                GROUP BY channel
                ORDER BY count DESC
            ''', (user_id, start_date.isoformat()))
            
            channel_counts = cursor.fetchall()
            preferred_channels = [channel for channel, count in channel_counts[:3]]
            
            # 最後のアクティビティ
            cursor.execute('''
                SELECT MAX(read_at) as last_read
                FROM notification_stats 
                WHERE user_id = ? AND read_at IS NOT NULL
            ''', (user_id,))
            
            last_read_result = cursor.fetchone()
            last_activity = None
            if last_read_result and last_read_result[0]:
                last_activity = datetime.fromisoformat(last_read_result[0])
            
            conn.close()
            
            # エンゲージメント計算
            engagement_rate = 0.0
            if total > 0:
                engagement_rate = ((read_count + clicked_count) / (total * 2)) * 100
            
            return UserEngagement(
                user_id=user_id,
                total_notifications=total or 0,
                read_notifications=read_count or 0,
                clicked_notifications=clicked_count or 0,
                engagement_rate=engagement_rate,
                preferred_channels=preferred_channels,
                response_time_avg=avg_response_time or 0.0,
                last_activity=last_activity
            )
    
    def get_channel_performance(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """チャンネル別パフォーマンスを取得"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    channel,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN delivered_at IS NOT NULL THEN 1 END) as delivered,
                    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
                    COUNT(CASE WHEN failed_at IS NOT NULL THEN 1 END) as failed,
                    AVG(CASE WHEN delivery_time_ms IS NOT NULL THEN delivery_time_ms END) as avg_delivery_time,
                    AVG(CASE WHEN read_time_ms IS NOT NULL THEN read_time_ms END) as avg_read_time
                FROM notification_stats 
                WHERE sent_at >= ?
                GROUP BY channel
            ''', (start_date.isoformat(),))
            
            results = cursor.fetchall()
            conn.close()
            
            channel_performance = {}
            for row in results:
                channel, total_sent, delivered, read, clicked, failed, avg_delivery_time, avg_read_time = row
                
                delivery_rate = (delivered / total_sent * 100) if total_sent > 0 else 0
                read_rate = (read / total_sent * 100) if total_sent > 0 else 0
                click_rate = (clicked / total_sent * 100) if total_sent > 0 else 0
                failure_rate = (failed / total_sent * 100) if total_sent > 0 else 0
                
                channel_performance[channel] = {
                    "total_sent": total_sent,
                    "delivered": delivered,
                    "read": read,
                    "clicked": clicked,
                    "failed": failed,
                    "delivery_rate": round(delivery_rate, 2),
                    "read_rate": round(read_rate, 2),
                    "click_rate": round(click_rate, 2),
                    "failure_rate": round(failure_rate, 2),
                    "avg_delivery_time_ms": round(avg_delivery_time or 0, 2),
                    "avg_read_time_ms": round(avg_read_time or 0, 2)
                }
            
            return channel_performance
    
    def get_notification_trends(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """通知トレンドを取得"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 日別統計
            cursor.execute('''
                SELECT 
                    DATE(sent_at) as date,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN delivered_at IS NOT NULL THEN 1 END) as delivered,
                    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked
                FROM notification_stats 
                WHERE sent_at >= ?
                GROUP BY DATE(sent_at)
                ORDER BY date
            ''', (start_date.isoformat(),))
            
            daily_trends = []
            for row in cursor.fetchall():
                date, total_sent, delivered, read, clicked = row
                daily_trends.append({
                    "date": date,
                    "total_sent": total_sent,
                    "delivered": delivered,
                    "read": read,
                    "clicked": clicked,
                    "delivery_rate": round((delivered / total_sent * 100) if total_sent > 0 else 0, 2),
                    "read_rate": round((read / total_sent * 100) if total_sent > 0 else 0, 2)
                })
            
            # 時間別統計
            cursor.execute('''
                SELECT 
                    strftime('%H', sent_at) as hour,
                    COUNT(*) as count
                FROM notification_stats 
                WHERE sent_at >= ?
                GROUP BY strftime('%H', sent_at)
                ORDER BY hour
            ''', (start_date.isoformat(),))
            
            hourly_trends = []
            for row in cursor.fetchall():
                hour, count = row
                hourly_trends.append({
                    "hour": int(hour),
                    "count": count
                })
            
            conn.close()
            
            return {
                "daily_trends": daily_trends,
                "hourly_trends": hourly_trends
            }
    
    def get_top_performing_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """パフォーマンス上位の通知を取得"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    notification_id,
                    notification_type,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read_count,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_count,
                    AVG(CASE WHEN read_time_ms IS NOT NULL THEN read_time_ms END) as avg_read_time
                FROM notification_stats 
                WHERE sent_at >= date('now', '-30 days')
                GROUP BY notification_id, notification_type
                HAVING total_sent >= 5
                ORDER BY (read_count + clicked_count) DESC, read_count DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            top_notifications = []
            for row in results:
                notification_id, notification_type, total_sent, read_count, clicked_count, avg_read_time = row
                engagement_rate = ((read_count + clicked_count) / total_sent * 100) if total_sent > 0 else 0
                
                top_notifications.append({
                    "notification_id": notification_id,
                    "notification_type": notification_type,
                    "total_sent": total_sent,
                    "read_count": read_count,
                    "clicked_count": clicked_count,
                    "engagement_rate": round(engagement_rate, 2),
                    "avg_read_time_ms": round(avg_read_time or 0, 2)
                })
            
            return top_notifications
    
    def generate_analytics_report(self, days: int = 30) -> Dict[str, Any]:
        """分析レポートを生成"""
        logger.info(f"Generating analytics report for {days} days")
        
        # 基本メトリクス
        metrics = self.get_notification_metrics(days=days)
        
        # チャンネル別パフォーマンス
        channel_performance = self.get_channel_performance(days)
        
        # トレンド分析
        trends = self.get_notification_trends(days)
        
        # トップパフォーマンス通知
        top_notifications = self.get_top_performing_notifications()
        
        report = {
            "report_period": {
                "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "days": days
            },
            "overall_metrics": {
                "total_sent": metrics.total_sent,
                "total_delivered": metrics.total_delivered,
                "total_read": metrics.total_read,
                "total_clicked": metrics.total_clicked,
                "total_failed": metrics.total_failed,
                "delivery_rate": round(metrics.delivery_rate, 2),
                "read_rate": round(metrics.read_rate, 2),
                "click_rate": round(metrics.click_rate, 2),
                "failure_rate": round(metrics.failure_rate, 2),
                "avg_delivery_time_ms": round(metrics.avg_delivery_time, 2)
            },
            "channel_performance": channel_performance,
            "trends": trends,
            "top_performing_notifications": top_notifications,
            "recommendations": self._generate_recommendations(metrics, channel_performance, trends)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: NotificationMetrics, 
                                channel_performance: Dict[str, Dict[str, Any]], 
                                trends: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        # 配信率の推奨
        if metrics.delivery_rate < 90:
            recommendations.append("配信率が90%を下回っています。チャンネル設定とネットワーク接続を確認してください。")
        
        # 読了率の推奨
        if metrics.read_rate < 50:
            recommendations.append("読了率が50%を下回っています。通知内容とタイミングの最適化を検討してください。")
        
        # チャンネル別推奨
        for channel, perf in channel_performance.items():
            if perf["failure_rate"] > 10:
                recommendations.append(f"{channel}チャンネルの失敗率が10%を超えています。設定を見直してください。")
        
        # 時間帯推奨
        hourly_trends = trends.get("hourly_trends", [])
        if hourly_trends:
            peak_hours = sorted(hourly_trends, key=lambda x: x["count"], reverse=True)[:3]
            recommendations.append(f"通知のピーク時間帯: {[h['hour'] for h in peak_hours]}時。この時間帯での配信を最適化してください。")
        
        return recommendations

# グローバルインスタンス
analytics = NotificationAnalytics()

def main():
    """テスト用メイン関数"""
    # テストイベントの記録
    test_event = NotificationEvent(
        id="test_event_1",
        notification_id="test_notification_1",
        event_type=NotificationStatus.SENT,
        timestamp=datetime.now(),
        channel=ChannelType.SLACK,
        user_id="test_user",
        metadata={"delivery_time_ms": 150}
    )
    
    analytics.record_event(test_event)
    
    # 分析レポートの生成
    report = analytics.generate_analytics_report(days=7)
    print("Analytics Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
