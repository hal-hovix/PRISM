#!/usr/bin/env python3
"""
PRISM Multi-Channel Notification System
マルチチャンネル通知システム - Slack・メール・SMS・Webhook対応
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
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

class ChannelType(Enum):
    """通知チャンネルタイプ"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"
    DISCORD = "discord"
    TEAMS = "teams"

class DeliveryStatus(Enum):
    """配信ステータス"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"

@dataclass
class ChannelConfig:
    """チャンネル設定"""
    channel_type: ChannelType
    enabled: bool = True
    priority: int = 1  # 1=最高優先度
    retry_count: int = 3
    retry_delay: int = 60  # 秒
    timeout: int = 30  # 秒
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationRequest:
    """通知リクエスト"""
    id: str
    title: str
    content: str
    priority: str = "medium"
    urgency: str = "medium"
    channels: List[ChannelType] = field(default_factory=list)
    user_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeliveryResult:
    """配信結果"""
    channel: ChannelType
    status: DeliveryStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    delivery_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class EmailChannel:
    """メールチャンネル"""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user")
        self.smtp_password = config.get("smtp_password")
        self.from_email = config.get("from_email")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
    
    async def send(self, request: NotificationRequest, content: str) -> DeliveryResult:
        """メール送信"""
        start_time = time.time()
        
        try:
            # メール作成
            msg = MIMEMultipart("alternative")
            msg["Subject"] = request.title
            msg["From"] = self.from_email
            msg["To"] = request.metadata.get("to_email", self.from_email)
            
            # HTMLコンテンツ
            html_content = f"""
            <html>
            <body>
                <h2>{request.title}</h2>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px;">
                    {content}
                </div>
                <hr>
                <p><em>PRISM v2.0.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
            </body>
            </html>
            """
            
            part1 = MIMEText(content, "plain")
            part2 = MIMEText(html_content, "html")
            
            msg.attach(part1)
            msg.attach(part2)
            
            # SMTP接続
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, msg["To"], msg.as_string())
            server.quit()
            
            delivery_time = int((time.time() - start_time) * 1000)
            
            return DeliveryResult(
                channel=ChannelType.EMAIL,
                status=DeliveryStatus.SENT,
                message_id=f"email_{request.id}",
                delivery_time_ms=delivery_time
            )
            
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return DeliveryResult(
                channel=ChannelType.EMAIL,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )

class SlackChannel:
    """Slackチャンネル"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get("webhook_url")
        self.bot_token = config.get("bot_token")
        self.default_channel = config.get("default_channel", "#general")
    
    async def send(self, request: NotificationRequest, content: str) -> DeliveryResult:
        """Slack送信"""
        start_time = time.time()
        
        try:
            # Slackメッセージ作成
            payload = {
                "text": request.title,
                "channel": request.metadata.get("channel", self.default_channel),
                "username": "PRISM Bot",
                "icon_emoji": ":robot_face:",
                "attachments": [
                    {
                        "color": self._get_color_by_priority(request.priority),
                        "fields": [
                            {
                                "title": "内容",
                                "value": content,
                                "short": False
                            },
                            {
                                "title": "優先度",
                                "value": request.priority,
                                "short": True
                            },
                            {
                                "title": "緊急度",
                                "value": request.urgency,
                                "short": True
                            }
                        ],
                        "footer": "PRISM v2.0.0",
                        "ts": int(time.time())
                    }
                ]
            }
            
            # Webhook送信
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            delivery_time = int((time.time() - start_time) * 1000)
            
            return DeliveryResult(
                channel=ChannelType.SLACK,
                status=DeliveryStatus.SENT,
                message_id=f"slack_{request.id}",
                delivery_time_ms=delivery_time,
                metadata={"response": response.text}
            )
            
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return DeliveryResult(
                channel=ChannelType.SLACK,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def _get_color_by_priority(self, priority: str) -> str:
        """優先度に応じた色を取得"""
        colors = {
            "low": "good",
            "medium": "warning",
            "high": "danger",
            "critical": "danger"
        }
        return colors.get(priority.lower(), "good")

class WebhookChannel:
    """Webhookチャンネル"""
    
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get("webhook_url")
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.auth_token = config.get("auth_token")
    
    async def send(self, request: NotificationRequest, content: str) -> DeliveryResult:
        """Webhook送信"""
        start_time = time.time()
        
        try:
            # Webhookペイロード作成
            payload = {
                "id": request.id,
                "title": request.title,
                "content": content,
                "priority": request.priority,
                "urgency": request.urgency,
                "timestamp": datetime.now().isoformat(),
                "source": "PRISM",
                "metadata": request.metadata
            }
            
            # ヘッダー設定
            headers = self.headers.copy()
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Webhook送信
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            delivery_time = int((time.time() - start_time) * 1000)
            
            return DeliveryResult(
                channel=ChannelType.WEBHOOK,
                status=DeliveryStatus.SENT,
                message_id=f"webhook_{request.id}",
                delivery_time_ms=delivery_time,
                metadata={"response": response.text}
            )
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return DeliveryResult(
                channel=ChannelType.WEBHOOK,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )

class SMSChannel:
    """SMSチャンネル（Twilio対応）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.account_sid = config.get("account_sid")
        self.auth_token = config.get("auth_token")
        self.from_number = config.get("from_number")
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    async def send(self, request: NotificationRequest, content: str) -> DeliveryResult:
        """SMS送信"""
        start_time = time.time()
        
        try:
            to_number = request.metadata.get("to_number")
            if not to_number:
                raise ValueError("SMS requires 'to_number' in metadata")
            
            # SMSメッセージ作成（160文字制限）
            sms_content = f"{request.title}: {content}"[:160]
            
            # Twilio API送信
            auth = (self.account_sid, self.auth_token)
            data = {
                "From": self.from_number,
                "To": to_number,
                "Body": sms_content
            }
            
            response = requests.post(
                self.api_url,
                data=data,
                auth=auth,
                timeout=30
            )
            response.raise_for_status()
            
            delivery_time = int((time.time() - start_time) * 1000)
            response_data = response.json()
            
            return DeliveryResult(
                channel=ChannelType.SMS,
                status=DeliveryStatus.SENT,
                message_id=response_data.get("sid"),
                delivery_time_ms=delivery_time,
                metadata={"twilio_response": response_data}
            )
            
        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            return DeliveryResult(
                channel=ChannelType.SMS,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )

class MultiChannelNotificationManager:
    """マルチチャンネル通知管理"""
    
    def __init__(self):
        self.channels: Dict[ChannelType, ChannelConfig] = {}
        self.channel_handlers: Dict[ChannelType, Any] = {}
        self.lock = Lock()
        
        # デフォルトチャンネル設定の初期化
        self._initialize_default_channels()
        
        logger.info("MultiChannelNotificationManager initialized")
    
    def _initialize_default_channels(self):
        """デフォルトチャンネル設定の初期化"""
        # 環境変数から設定を読み込み
        default_configs = {
            ChannelType.EMAIL: ChannelConfig(
                channel_type=ChannelType.EMAIL,
                enabled=bool(os.getenv("REPORT_EMAIL_SMTP_HOST")),
                priority=2,
                config={
                    "smtp_host": os.getenv("REPORT_EMAIL_SMTP_HOST"),
                    "smtp_port": int(os.getenv("REPORT_EMAIL_SMTP_PORT", 587)),
                    "smtp_user": os.getenv("REPORT_EMAIL_SMTP_USER"),
                    "smtp_password": os.getenv("REPORT_EMAIL_SMTP_PASSWORD"),
                    "from_email": os.getenv("REPORT_EMAIL_FROM"),
                    "use_tls": True
                }
            ),
            ChannelType.SLACK: ChannelConfig(
                channel_type=ChannelType.SLACK,
                enabled=bool(os.getenv("SLACK_WEBHOOK_URL")),
                priority=1,
                config={
                    "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                    "bot_token": os.getenv("SLACK_BOT_TOKEN"),
                    "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
                }
            ),
            ChannelType.WEBHOOK: ChannelConfig(
                channel_type=ChannelType.WEBHOOK,
                enabled=False,  # デフォルトでは無効
                priority=3,
                config={}
            ),
            ChannelType.SMS: ChannelConfig(
                channel_type=ChannelType.SMS,
                enabled=False,  # デフォルトでは無効
                priority=4,
                config={}
            )
        }
        
        for channel_type, config in default_configs.items():
            self.add_channel(channel_type, config)
    
    def add_channel(self, channel_type: ChannelType, config: ChannelConfig):
        """チャンネルを追加"""
        with self.lock:
            self.channels[channel_type] = config
            
            # チャンネルハンドラーの初期化
            if channel_type == ChannelType.EMAIL:
                self.channel_handlers[channel_type] = EmailChannel(config.config)
            elif channel_type == ChannelType.SLACK:
                self.channel_handlers[channel_type] = SlackChannel(config.config)
            elif channel_type == ChannelType.WEBHOOK:
                self.channel_handlers[channel_type] = WebhookChannel(config.config)
            elif channel_type == ChannelType.SMS:
                self.channel_handlers[channel_type] = SMSChannel(config.config)
            
            logger.info(f"Added channel: {channel_type.value}")
    
    def update_channel_config(self, channel_type: ChannelType, updates: Dict[str, Any]):
        """チャンネル設定を更新"""
        with self.lock:
            if channel_type in self.channels:
                config = self.channels[channel_type]
                for key, value in updates.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                # ハンドラーの再初期化
                if channel_type in self.channel_handlers:
                    if channel_type == ChannelType.EMAIL:
                        self.channel_handlers[channel_type] = EmailChannel(config.config)
                    elif channel_type == ChannelType.SLACK:
                        self.channel_handlers[channel_type] = SlackChannel(config.config)
                    elif channel_type == ChannelType.WEBHOOK:
                        self.channel_handlers[channel_type] = WebhookChannel(config.config)
                    elif channel_type == ChannelType.SMS:
                        self.channel_handlers[channel_type] = SMSChannel(config.config)
                
                logger.info(f"Updated channel config: {channel_type.value}")
    
    async def send_notification(self, request: NotificationRequest) -> List[DeliveryResult]:
        """通知を送信"""
        logger.info(f"Sending notification: {request.id}")
        
        # 送信チャンネルの決定
        channels_to_send = self._determine_channels(request)
        
        if not channels_to_send:
            logger.warning("No channels available for notification")
            return []
        
        # 並列送信
        tasks = []
        for channel_type in channels_to_send:
            task = self._send_to_channel(request, channel_type)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果の処理
        delivery_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Channel {channels_to_send[i].value} failed: {result}")
                delivery_results.append(DeliveryResult(
                    channel=channels_to_send[i],
                    status=DeliveryStatus.FAILED,
                    error_message=str(result)
                ))
            else:
                delivery_results.append(result)
        
        # 成功したチャンネルの記録
        successful_channels = [r.channel for r in delivery_results if r.status == DeliveryStatus.SENT]
        logger.info(f"Notification sent successfully to: {[c.value for c in successful_channels]}")
        
        return delivery_results
    
    def _determine_channels(self, request: NotificationRequest) -> List[ChannelType]:
        """送信チャンネルを決定"""
        # リクエストで指定されたチャンネル
        if request.channels:
            available_channels = [c for c in request.channels if c in self.channels and self.channels[c].enabled]
            if available_channels:
                return available_channels
        
        # 優先度に基づく自動選択
        enabled_channels = [
            (channel_type, config) 
            for channel_type, config in self.channels.items() 
            if config.enabled
        ]
        
        # 優先度順でソート
        enabled_channels.sort(key=lambda x: x[1].priority)
        
        # 優先度に応じてチャンネルを選択
        selected_channels = []
        priority_value = self._get_priority_value(request.priority)
        
        for channel_type, config in enabled_channels:
            if priority_value >= config.priority:
                selected_channels.append(channel_type)
        
        return selected_channels
    
    def _get_priority_value(self, priority: str) -> int:
        """優先度の数値化"""
        priority_values = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        return priority_values.get(priority.lower(), 2)
    
    async def _send_to_channel(self, request: NotificationRequest, channel_type: ChannelType) -> DeliveryResult:
        """チャンネルに送信"""
        if channel_type not in self.channel_handlers:
            return DeliveryResult(
                channel=channel_type,
                status=DeliveryStatus.FAILED,
                error_message="Channel handler not available"
            )
        
        handler = self.channel_handlers[channel_type]
        config = self.channels[channel_type]
        
        # リトライロジック
        last_error = None
        for attempt in range(config.retry_count):
            try:
                result = await handler.send(request, request.content)
                if result.status == DeliveryStatus.SENT:
                    return result
                last_error = result.error_message
                
                if attempt < config.retry_count - 1:
                    await asyncio.sleep(config.retry_delay)
                    
            except Exception as e:
                last_error = str(e)
                if attempt < config.retry_count - 1:
                    await asyncio.sleep(config.retry_delay)
        
        return DeliveryResult(
            channel=channel_type,
            status=DeliveryStatus.FAILED,
            error_message=f"Failed after {config.retry_count} attempts: {last_error}"
        )
    
    def get_channel_status(self) -> Dict[str, Dict[str, Any]]:
        """チャンネルステータスを取得"""
        with self.lock:
            status = {}
            for channel_type, config in self.channels.items():
                status[channel_type.value] = {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "retry_count": config.retry_count,
                    "retry_delay": config.retry_delay,
                    "timeout": config.timeout,
                    "handler_available": channel_type in self.channel_handlers
                }
            return status
    
    def test_channel(self, channel_type: ChannelType) -> DeliveryResult:
        """チャンネルのテスト"""
        if channel_type not in self.channel_handlers:
            return DeliveryResult(
                channel=channel_type,
                status=DeliveryStatus.FAILED,
                error_message="Channel handler not available"
            )
        
        # テスト通知リクエスト
        test_request = NotificationRequest(
            id=f"test_{int(time.time())}",
            title="チャンネルテスト",
            content="これはテスト通知です。",
            priority="medium",
            urgency="low",
            metadata={"test": True}
        )
        
        # 同期テスト（簡易版）
        try:
            handler = self.channel_handlers[channel_type]
            # 非同期ハンドラーを同期で実行
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(handler.send(test_request, test_request.content))
            loop.close()
            return result
        except Exception as e:
            return DeliveryResult(
                channel=channel_type,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )

# グローバルインスタンス
multi_channel_manager = MultiChannelNotificationManager()

def main():
    """テスト用メイン関数"""
    # テスト通知リクエスト
    test_request = NotificationRequest(
        id="test_notification_1",
        title="マルチチャンネルテスト",
        content="これはマルチチャンネル通知のテストです。",
        priority="high",
        urgency="medium",
        channels=[ChannelType.SLACK, ChannelType.EMAIL]
    )
    
    # 通知送信テスト
    import asyncio
    results = asyncio.run(multi_channel_manager.send_notification(test_request))
    
    print("Multi-channel notification results:")
    for result in results:
        print(f"Channel: {result.channel.value}, Status: {result.status.value}")

if __name__ == "__main__":
    main()
