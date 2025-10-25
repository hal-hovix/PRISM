"""
通知設定管理APIエンドポイント
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from ..core.security import verify_api_key
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

# 通知設定
NOTIFICATION_CONFIG_FILE = "/tmp/notification_settings.json"

class NotificationSettings(BaseModel):
    email_enabled: bool = True
    email_frequency: str = "daily"  # daily, weekly, monthly, custom
    email_time: str = "09:00"  # HH:MM format
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    task_reminders: bool = True
    habit_notifications: bool = True
    system_alerts: bool = True
    custom_notifications: Dict[str, Any] = {}

class NotificationManager:
    """通知管理クラス"""
    
    def __init__(self):
        self.settings = self._load_settings()
        self.smtp_config = self._get_smtp_config()
    
    def _load_settings(self) -> NotificationSettings:
        """通知設定を読み込み"""
        try:
            if os.path.exists(NOTIFICATION_CONFIG_FILE):
                with open(NOTIFICATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return NotificationSettings(**data)
            else:
                # デフォルト設定を作成
                default_settings = NotificationSettings()
                self._save_settings(default_settings)
                return default_settings
        except Exception as e:
            logger.error(f"Error loading notification settings: {e}")
            return NotificationSettings()
    
    def _save_settings(self, settings: NotificationSettings):
        """通知設定を保存"""
        try:
            os.makedirs(os.path.dirname(NOTIFICATION_CONFIG_FILE), exist_ok=True)
            with open(NOTIFICATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving notification settings: {e}")
    
    def _get_smtp_config(self) -> Dict[str, str]:
        """SMTP設定を取得"""
        return {
            "host": os.getenv("REPORT_EMAIL_SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("REPORT_EMAIL_SMTP_PORT", "587")),
            "user": os.getenv("REPORT_EMAIL_SMTP_USER", ""),
            "password": os.getenv("REPORT_EMAIL_SMTP_PASSWORD", ""),
            "from_email": os.getenv("REPORT_EMAIL_FROM", ""),
            "to_email": os.getenv("REPORT_EMAIL_TO", "")
        }
    
    def send_email_notification(self, subject: str, content: str, html_content: str = None) -> bool:
        """メール通知を送信"""
        if not self.settings.email_enabled:
            logger.info("Email notifications are disabled")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config["from_email"]
            msg['To'] = self.smtp_config["to_email"]
            
            # テキスト部分
            text_part = MIMEText(content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML部分（提供されている場合）
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # SMTP接続と送信
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["user"], self.smtp_config["password"])
                server.send_message(msg)
            
            logger.info(f"Email notification sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def send_slack_notification(self, message: str, channel: str = None, blocks: list = None, attachments: list = None) -> bool:
        """Slack通知を送信（リッチフォーマット対応）"""
        if not self.settings.slack_enabled or not self.settings.slack_webhook_url:
            logger.info("Slack notifications are disabled or not configured")
            return False
        
        try:
            import requests
            
            webhook_url = self.settings.slack_webhook_url
            target_channel = channel or self.settings.slack_channel
            
            payload = {
                "text": message,
                "channel": target_channel
            }
            
            # リッチフォーマット対応
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent to {target_channel}")
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
    
    def create_slack_habit_blocks(self, habit_data: Dict[str, Any]) -> list:
        """習慣通知用のSlackブロックを作成"""
        status_emoji = "✅" if habit_data.get('completed', False) else "❌"
        status_text = "完了" if habit_data.get('completed', False) else "未完了"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📈 習慣進捗: {habit_data.get('name', '無題の習慣')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*今日の状況:*\n{status_emoji} {status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*連続日数:*\n{habit_data.get('streak', 0)}日"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*達成率:*\n{habit_data.get('completion_rate', 0)}%"
                    }
                ]
            }
        ]
        
        if habit_data.get('description'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*詳細:*\n{habit_data.get('description', '詳細なし')}"
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
    
    def create_slack_system_blocks(self, alert_type: str, message: str, details: Dict[str, Any] = None) -> list:
        """システムアラート用のSlackブロックを作成"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ システムアラート: {alert_type}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*メッセージ:*\n{message}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*発生時刻:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        if details:
            details_text = "\n".join([f"• {k}: {v}" for k, v in details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*詳細:*\n{details_text}"
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
        if not self.settings.task_reminders:
            return False
        
        subject = f"🔔 タスクリマインダー: {task_data.get('title', '無題のタスク')}"
        
        content = f"""
タスクリマインダー

タスク名: {task_data.get('title', '無題のタスク')}
期日: {task_data.get('due_date', '未設定')}
ステータス: {task_data.get('status', '未設定')}

詳細:
{task_data.get('content', '詳細なし')}

---
PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management
        """.strip()
        
        html_content = f"""
        <html>
        <body>
            <h2>🔔 タスクリマインダー</h2>
            <p><strong>タスク名:</strong> {task_data.get('title', '無題のタスク')}</p>
            <p><strong>期日:</strong> {task_data.get('due_date', '未設定')}</p>
            <p><strong>ステータス:</strong> {task_data.get('status', '未設定')}</p>
            <hr>
            <p><strong>詳細:</strong></p>
            <p>{task_data.get('content', '詳細なし')}</p>
            <hr>
            <p><em>PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management</em></p>
        </body>
        </html>
        """
        
        # メール送信
        email_sent = self.send_email_notification(subject, content, html_content)
        
        # Slack送信（リッチフォーマット）
        slack_blocks = self.create_slack_task_blocks(task_data)
        slack_message = f"🔔 *タスクリマインダー*\n*タスク名:* {task_data.get('title', '無題のタスク')}\n*期日:* {task_data.get('due_date', '未設定')}\n*ステータス:* {task_data.get('status', '未設定')}"
        slack_sent = self.send_slack_notification(slack_message, blocks=slack_blocks)
        
        return email_sent or slack_sent
    
    def send_habit_notification(self, habit_data: Dict[str, Any]) -> bool:
        """習慣通知を送信"""
        if not self.settings.habit_notifications:
            return False
        
        subject = f"📈 習慣進捗: {habit_data.get('name', '無題の習慣')}"
        
        content = f"""
習慣進捗通知

習慣名: {habit_data.get('name', '無題の習慣')}
今日の状況: {'完了' if habit_data.get('completed', False) else '未完了'}
連続日数: {habit_data.get('streak', 0)}日
達成率: {habit_data.get('completion_rate', 0)}%

詳細:
{habit_data.get('description', '詳細なし')}

---
PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management
        """.strip()
        
        html_content = f"""
        <html>
        <body>
            <h2>📈 習慣進捗通知</h2>
            <p><strong>習慣名:</strong> {habit_data.get('name', '無題の習慣')}</p>
            <p><strong>今日の状況:</strong> {'✅ 完了' if habit_data.get('completed', False) else '❌ 未完了'}</p>
            <p><strong>連続日数:</strong> {habit_data.get('streak', 0)}日</p>
            <p><strong>達成率:</strong> {habit_data.get('completion_rate', 0)}%</p>
            <hr>
            <p><strong>詳細:</strong></p>
            <p>{habit_data.get('description', '詳細なし')}</p>
            <hr>
            <p><em>PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management</em></p>
        </body>
        </html>
        """
        
        # メール送信
        email_sent = self.send_email_notification(subject, content, html_content)
        
        # Slack送信（リッチフォーマット）
        slack_blocks = self.create_slack_habit_blocks(habit_data)
        status_emoji = "✅" if habit_data.get('completed', False) else "❌"
        slack_message = f"📈 *習慣進捗通知*\n*習慣名:* {habit_data.get('name', '無題の習慣')}\n*今日の状況:* {status_emoji} {'完了' if habit_data.get('completed', False) else '未完了'}\n*連続日数:* {habit_data.get('streak', 0)}日\n*達成率:* {habit_data.get('completion_rate', 0)}%"
        slack_sent = self.send_slack_notification(slack_message, blocks=slack_blocks)
        
        return email_sent or slack_sent
    
    def send_system_alert(self, alert_type: str, message: str, details: Dict[str, Any] = None) -> bool:
        """システムアラートを送信"""
        if not self.settings.system_alerts:
            return False
        
        subject = f"⚠️ システムアラート: {alert_type}"
        
        content = f"""
システムアラート

アラートタイプ: {alert_type}
メッセージ: {message}
発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

詳細:
{json.dumps(details or {}, ensure_ascii=False, indent=2)}

---
PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management
        """.strip()
        
        html_content = f"""
        <html>
        <body>
            <h2>⚠️ システムアラート</h2>
            <p><strong>アラートタイプ:</strong> {alert_type}</p>
            <p><strong>メッセージ:</strong> {message}</p>
            <p><strong>発生時刻:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <p><strong>詳細:</strong></p>
            <pre>{json.dumps(details or {}, ensure_ascii=False, indent=2)}</pre>
            <hr>
            <p><em>PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management</em></p>
        </body>
        </html>
        """
        
        # メール送信
        email_sent = self.send_email_notification(subject, content, html_content)
        
        # Slack送信（リッチフォーマット）
        slack_blocks = self.create_slack_system_blocks(alert_type, message, details)
        slack_message = f"⚠️ *システムアラート*\n*タイプ:* {alert_type}\n*メッセージ:* {message}\n*時刻:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        slack_sent = self.send_slack_notification(slack_message, blocks=slack_blocks)
        
        return email_sent or slack_sent

# グローバル通知管理インスタンス
notification_manager = NotificationManager()

# レスポンスモデル
class NotificationResponse(BaseModel):
    success: bool
    message: str
    notification_type: str
    timestamp: str

class SettingsResponse(BaseModel):
    settings: NotificationSettings
    timestamp: str

@router.get("/settings")
async def get_notification_settings(
    _=Depends(verify_api_key)
) -> SettingsResponse:
    """通知設定を取得"""
    try:
        logger.info("Getting notification settings")
        
        return SettingsResponse(
            settings=notification_manager.settings,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@router.post("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    _=Depends(verify_api_key)
) -> SettingsResponse:
    """通知設定を更新"""
    try:
        logger.info("Updating notification settings")
        
        notification_manager.settings = settings
        notification_manager._save_settings(settings)
        
        return SettingsResponse(
            settings=settings,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.post("/test/email")
async def test_email_notification(
    _=Depends(verify_api_key)
) -> NotificationResponse:
    """メール通知のテスト"""
    try:
        logger.info("Testing email notification")
        
        subject = "🧪 PRISM メール通知テスト"
        content = """
これはPRISM v2.0.0のメール通知テストです。

通知システムが正常に動作していることを確認できました。

---
PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management
        """.strip()
        
        success = notification_manager.send_email_notification(subject, content)
        
        return NotificationResponse(
            success=success,
            message="メール通知テストが完了しました" if success else "メール通知テストに失敗しました",
            notification_type="email_test",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error testing email notification: {e}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")

@router.post("/test/slack")
async def test_slack_notification(
    _=Depends(verify_api_key)
) -> NotificationResponse:
    """Slack通知のテスト"""
    try:
        logger.info("Testing Slack notification")
        
        message = "🧪 *PRISM Slack通知テスト*\n通知システムが正常に動作していることを確認できました。"
        
        success = notification_manager.send_slack_notification(message)
        
        return NotificationResponse(
            success=success,
            message="Slack通知テストが完了しました" if success else "Slack通知テストに失敗しました（設定を確認してください）",
            notification_type="slack_test",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error testing Slack notification: {e}")
        raise HTTPException(status_code=500, detail=f"Slack test failed: {str(e)}")

@router.post("/task-reminder")
async def send_task_reminder(
    task_data: Dict[str, Any],
    _=Depends(verify_api_key)
) -> NotificationResponse:
    """タスクリマインダーを送信"""
    try:
        logger.info("Sending task reminder")
        
        success = notification_manager.send_task_reminder(task_data)
        
        return NotificationResponse(
            success=success,
            message="タスクリマインダーを送信しました" if success else "タスクリマインダーの送信に失敗しました",
            notification_type="task_reminder",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error sending task reminder: {e}")
        raise HTTPException(status_code=500, detail=f"Task reminder failed: {str(e)}")

@router.post("/habit-notification")
async def send_habit_notification(
    habit_data: Dict[str, Any],
    _=Depends(verify_api_key)
) -> NotificationResponse:
    """習慣通知を送信"""
    try:
        logger.info("Sending habit notification")
        
        success = notification_manager.send_habit_notification(habit_data)
        
        return NotificationResponse(
            success=success,
            message="習慣通知を送信しました" if success else "習慣通知の送信に失敗しました",
            notification_type="habit_notification",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error sending habit notification: {e}")
        raise HTTPException(status_code=500, detail=f"Habit notification failed: {str(e)}")

@router.post("/system-alert")
async def send_system_alert(
    alert_type: str = Query(..., description="アラートタイプ"),
    message: str = Query(..., description="アラートメッセージ"),
    details: str = Query(default="{}", description="詳細情報（JSON）"),
    _=Depends(verify_api_key)
) -> NotificationResponse:
    """システムアラートを送信"""
    try:
        logger.info(f"Sending system alert: {alert_type}")
        
        details_dict = json.loads(details) if details else {}
        success = notification_manager.send_system_alert(alert_type, message, details_dict)
        
        return NotificationResponse(
            success=success,
            message="システムアラートを送信しました" if success else "システムアラートの送信に失敗しました",
            notification_type="system_alert",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error sending system alert: {e}")
        raise HTTPException(status_code=500, detail=f"System alert failed: {str(e)}")

@router.get("/test")
async def test_notification_system(
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """通知システムのテスト"""
    try:
        logger.info("Testing notification system")
        
        # 設定確認
        settings = notification_manager.settings
        
        # テスト結果
        test_results = {
            "email_enabled": settings.email_enabled,
            "slack_enabled": settings.slack_enabled,
            "smtp_configured": bool(notification_manager.smtp_config["user"]),
            "slack_configured": bool(settings.slack_webhook_url),
            "settings_file_exists": os.path.exists(NOTIFICATION_CONFIG_FILE)
        }
        
        return {
            "status": "success",
            "test_results": test_results,
            "settings": settings.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing notification system: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
