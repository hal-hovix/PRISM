#!/usr/bin/env python3
"""
PRISM Notification Scheduler - Simplified Version
自動通知スケジューラー - タスク期日、習慣進捗、システムアラートの自動送信
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import schedule
import time
from threading import Thread

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 簡素化されたログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskData:
    """タスクデータ構造"""
    id: str
    title: str
    content: str
    due_date: Optional[str]
    status: str
    priority: str = "medium"
    category: str = "general"

@dataclass
class HabitData:
    """習慣データ構造"""
    id: str
    name: str
    description: str
    completed: bool
    streak: int
    completion_rate: float
    target_frequency: str = "daily"

class SimpleNotificationManager:
    """簡素化された通知管理"""
    
    def __init__(self):
        self.smtp_host = os.getenv("REPORT_EMAIL_SMTP_HOST")
        self.smtp_port = int(os.getenv("REPORT_EMAIL_SMTP_PORT", 465))
        self.smtp_user = os.getenv("REPORT_EMAIL_SMTP_USER")
        self.smtp_password = os.getenv("REPORT_EMAIL_SMTP_PASSWORD")
        self.from_email = os.getenv("REPORT_EMAIL_FROM")
        self.to_email = os.getenv("REPORT_EMAIL_TO")
        
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.slack_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
        
        logger.info("SimpleNotificationManager initialized")
    
    def send_slack_notification(self, message: str, blocks: list = None) -> bool:
        """Slack通知を送信"""
        if not self.slack_webhook_url:
            logger.info("Slack webhook URL not configured")
            return False
        
        try:
            import requests
            
            payload = {
                "text": message,
                "channel": self.slack_channel
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent to {self.slack_channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def create_slack_task_blocks(self, task_data: Dict[str, Any]) -> list:
        """タスクリマインダー用のSlackブロックを作成"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔔 タスクリマインダー: {task_data.get('title', '無題のタスク')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*期日:*\n{task_data.get('due_date', '未設定')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ステータス:*\n{task_data.get('status', '未設定')}"
                    }
                ]
            }
        ]
        
        if task_data.get('content'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*詳細:*\n{task_data.get('content', '詳細なし')}"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management"
                }
            ]
        })
        
        return blocks
    
    def send_task_reminder(self, task_data: Dict[str, Any]) -> bool:
        """タスクリマインダーを送信"""
        slack_blocks = self.create_slack_task_blocks(task_data)
        slack_message = f"🔔 *タスクリマインダー*\n*タスク名:* {task_data.get('title', '無題のタスク')}\n*期日:* {task_data.get('due_date', '未設定')}\n*ステータス:* {task_data.get('status', '未設定')}"
        
        return self.send_slack_notification(slack_message, blocks=slack_blocks)
    
    def send_system_alert(self, alert_type: str, message: str, details: Dict[str, Any] = None) -> bool:
        """システムアラートを送信"""
        slack_message = f"⚠️ *システムアラート*\n*タイプ:* {alert_type}\n*メッセージ:* {message}\n*時刻:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if details:
            details_text = "\n".join([f"• {k}: {v}" for k, v in details.items()])
            slack_message += f"\n*詳細:*\n{details_text}"
        
        return self.send_slack_notification(slack_message)

class NotificationScheduler:
    """自動通知スケジューラー"""
    
    def __init__(self):
        self.notification_manager = SimpleNotificationManager()
        self.notion_api_key = os.getenv("NOTION_API_KEY")
        self.notion_task_db_id = os.getenv("NOTION_TASK_DB_ID")
        self.notion_habit_db_id = os.getenv("NOTION_HABIT_DB_ID")
        
        logger.info("NotificationScheduler initialized")
    
    async def fetch_notion_data(self, database_id: str, filter_conditions: Dict = None) -> List[Dict]:
        """Notionデータベースからデータを取得"""
        if not self.notion_api_key or not database_id:
            logger.warning("Notion API key or database ID not configured")
            return []
        
        headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        payload = {
            "page_size": 100
        }
        
        if filter_conditions:
            payload["filter"] = filter_conditions
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        logger.error(f"Failed to fetch Notion data: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching Notion data: {e}")
            return []
    
    def extract_task_data(self, notion_page: Dict) -> Optional[TaskData]:
        """Notionページからタスクデータを抽出"""
        try:
            properties = notion_page.get("properties", {})
            
            # タイトル取得
            title_prop = properties.get("タイトル", {}).get("title", [])
            title = title_prop[0].get("text", {}).get("content", "無題のタスク") if title_prop else "無題のタスク"
            
            # 内容取得
            content_prop = properties.get("内容", {}).get("rich_text", [])
            content = "".join([text.get("text", {}).get("content", "") for text in content_prop])
            
            # 期日取得
            due_date_prop = properties.get("期日", {}).get("date", {})
            due_date = due_date_prop.get("start") if due_date_prop else None
            
            # ステータス取得
            status_prop = properties.get("ステータス", {}).get("select", {})
            status = status_prop.get("name", "未設定") if status_prop else "未設定"
            
            return TaskData(
                id=notion_page.get("id", ""),
                title=title,
                content=content,
                due_date=due_date,
                status=status
            )
        except Exception as e:
            logger.error(f"Error extracting task data: {e}")
            return None
    
    async def check_task_reminders(self):
        """タスクリマインダーのチェック"""
        logger.info("Checking task reminders...")
        
        if not self.notion_task_db_id:
            logger.warning("Task database ID not configured")
            return
        
        # 今日から3日後までのタスクを取得
        today = datetime.now().date()
        end_date = today + timedelta(days=3)
        
        filter_conditions = {
            "and": [
                {
                    "property": "期日",
                    "date": {
                        "on_or_after": today.isoformat()
                    }
                },
                {
                    "property": "期日",
                    "date": {
                        "on_or_before": end_date.isoformat()
                    }
                },
                {
                    "property": "ステータス",
                    "select": {
                        "does_not_equal": "完了"
                    }
                }
            ]
        }
        
        tasks_data = await self.fetch_notion_data(self.notion_task_db_id, filter_conditions)
        
        for task_page in tasks_data:
            task = self.extract_task_data(task_page)
            if not task or not task.due_date:
                continue
            
            due_date = datetime.fromisoformat(task.due_date.replace('Z', '+00:00')).date()
            days_until_due = (due_date - today).days
            
            # 通知タイミングのチェック
            if days_until_due in [1, 0]:  # 明日または今日
                task_data = {
                    "title": task.title,
                    "content": task.content,
                    "due_date": task.due_date,
                    "status": task.status
                }
                
                # 通知送信
                success = self.notification_manager.send_task_reminder(task_data)
                if success:
                    logger.info(f"Task reminder sent for: {task.title}")
                else:
                    logger.warning(f"Failed to send task reminder for: {task.title}")
    
    async def check_system_health(self):
        """システムヘルスチェック"""
        logger.info("Checking system health...")
        
        try:
            # API ヘルスチェック
            async with aiohttp.ClientSession() as session:
                async with session.get("http://PRISM-API:8000/healthz") as response:
                    if response.status != 200:
                        await self.send_system_alert(
                            "API Health Check Failed",
                            f"API returned status {response.status}",
                            {"status_code": response.status, "timestamp": datetime.now().isoformat()}
                        )
                        return
            
            logger.info("System health check completed successfully")
            
        except Exception as e:
            logger.error(f"System health check error: {e}")
            await self.send_system_alert(
                "System Health Check Error",
                f"Health check failed: {str(e)}",
                {"error": str(e), "timestamp": datetime.now().isoformat()}
            )
    
    async def send_system_alert(self, alert_type: str, message: str, details: Dict = None):
        """システムアラートを送信"""
        success = self.notification_manager.send_system_alert(alert_type, message, details)
        if success:
            logger.info(f"System alert sent: {alert_type}")
        else:
            logger.warning(f"Failed to send system alert: {alert_type}")
    
    def schedule_notifications(self):
        """通知スケジュールを設定"""
        # タスクリマインダー（毎日9:00）
        schedule.every().day.at("09:00").do(
            lambda: asyncio.run(self.check_task_reminders())
        )
        
        # システムヘルスチェック（30分ごと）
        schedule.every(30).minutes.do(
            lambda: asyncio.run(self.check_system_health())
        )
        
        logger.info("Notification schedule configured")
    
    def run_scheduler(self):
        """スケジューラーを実行"""
        logger.info("Starting notification scheduler...")
        
        self.schedule_notifications()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック

def main():
    """メイン関数"""
    scheduler = NotificationScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()