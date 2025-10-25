#!/usr/bin/env python3
"""
PRISM Notification Template System
通知テンプレートシステム - カスタマイズ可能な通知フォーマット
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from jinja2 import Template, Environment, BaseLoader
from threading import Lock

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """テンプレートタイプ"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"

class TemplateFormat(Enum):
    """テンプレートフォーマット"""
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    XML = "xml"

@dataclass
class TemplateVariable:
    """テンプレート変数"""
    name: str
    type: str
    description: str
    default_value: Any = None
    required: bool = True
    validation_pattern: Optional[str] = None

@dataclass
class NotificationTemplate:
    """通知テンプレート"""
    id: str
    name: str
    description: str
    template_type: TemplateType
    template_format: TemplateFormat
    content: str
    variables: List[TemplateVariable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class TemplateEngine:
    """テンプレートエンジン"""
    
    def __init__(self):
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # カスタムフィルターの追加
        self.env.filters['format_datetime'] = self._format_datetime
        self.env.filters['format_priority'] = self._format_priority
        self.env.filters['format_urgency'] = self._format_urgency
        self.env.filters['truncate'] = self._truncate
        self.env.filters['highlight'] = self._highlight
        
        logger.info("TemplateEngine initialized")
    
    def _format_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日時フォーマット"""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        return dt.strftime(format_str)
    
    def _format_priority(self, priority: str) -> str:
        """優先度フォーマット"""
        priority_emojis = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴"
        }
        return priority_emojis.get(priority.lower(), "⚪")
    
    def _format_urgency(self, urgency: str) -> str:
        """緊急度フォーマット"""
        urgency_emojis = {
            "low": "📅",
            "medium": "⏰",
            "high": "🚨",
            "urgent": "🚨🚨"
        }
        return urgency_emojis.get(urgency.lower(), "📋")
    
    def _truncate(self, text: str, length: int = 100, suffix: str = "...") -> str:
        """テキスト切り詰め"""
        if len(text) <= length:
            return text
        return text[:length-len(suffix)] + suffix
    
    def _highlight(self, text: str, keyword: str, class_name: str = "highlight") -> str:
        """キーワードハイライト"""
        if not keyword:
            return text
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(f'<span class="{class_name}">{keyword}</span>', text)
    
    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """テンプレートをレンダリング"""
        try:
            template = self.env.from_string(template_content)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_content

class NotificationTemplateManager:
    """通知テンプレート管理"""
    
    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
        self.template_engine = TemplateEngine()
        self.lock = Lock()
        
        # デフォルトテンプレートの初期化
        self._initialize_default_templates()
        
        logger.info("NotificationTemplateManager initialized")
    
    def _initialize_default_templates(self):
        """デフォルトテンプレートの初期化"""
        default_templates = [
            # Slack タスクリマインダーテンプレート
            NotificationTemplate(
                id="slack_task_reminder",
                name="Slack タスクリマインダー",
                description="Slack用のタスクリマインダーテンプレート",
                template_type=TemplateType.SLACK,
                template_format=TemplateFormat.JSON,
                content='''{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "{{ priority|format_priority }} {{ urgency|format_urgency }} タスクリマインダー: {{ title }}"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*期日:*\\n{{ due_date|format_datetime('%Y-%m-%d %H:%M') }}"
        },
        {
          "type": "mrkdwn",
          "text": "*ステータス:*\\n{{ status }}"
        },
        {
          "type": "mrkdwn",
          "text": "*優先度:*\\n{{ priority|format_priority }} {{ priority|title }}"
        },
        {
          "type": "mrkdwn",
          "text": "*緊急度:*\\n{{ urgency|format_urgency }} {{ urgency|title }}"
        }
      ]
    },
    {% if content %}
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*詳細:*\\n{{ content|truncate(500) }}"
      }
    },
    {% endif %}
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "PRISM v2.0.0 - {{ timestamp|format_datetime('%Y-%m-%d %H:%M:%S') }}"
        }
      ]
    }
  ]
}''',
                variables=[
                    TemplateVariable("title", "string", "タスクタイトル", required=True),
                    TemplateVariable("content", "string", "タスク内容", required=False),
                    TemplateVariable("due_date", "datetime", "期日", required=True),
                    TemplateVariable("status", "string", "ステータス", required=True),
                    TemplateVariable("priority", "string", "優先度", required=True),
                    TemplateVariable("urgency", "string", "緊急度", required=True),
                    TemplateVariable("timestamp", "datetime", "通知時刻", required=True)
                ]
            ),
            
            # メール システムアラートテンプレート
            NotificationTemplate(
                id="email_system_alert",
                name="メール システムアラート",
                description="メール用のシステムアラートテンプレート",
                template_type=TemplateType.EMAIL,
                template_format=TemplateFormat.HTML,
                content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>システムアラート - {{ alert_type }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: {{ priority_color }}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { padding: 20px; }
        .alert-info { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0; }
        .footer { background: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #666; }
        .priority-{{ priority }} { font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ priority|format_priority }} システムアラート: {{ alert_type }}</h1>
            <p>{{ urgency|format_urgency }} {{ urgency|title }} - {{ timestamp|format_datetime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
        
        <div class="content">
            <div class="alert-info">
                <h3>アラート詳細</h3>
                <p><strong>メッセージ:</strong> {{ message }}</p>
                {% if details %}
                <p><strong>詳細情報:</strong></p>
                <ul>
                {% for key, value in details.items() %}
                    <li><strong>{{ key }}:</strong> {{ value }}</li>
                {% endfor %}
                </ul>
                {% endif %}
            </div>
            
            {% if recommendations %}
            <div class="alert-info">
                <h3>推奨アクション</h3>
                <ul>
                {% for recommendation in recommendations %}
                    <li>{{ recommendation }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management</p>
            <p>このメールは自動送信されています。</p>
        </div>
    </div>
</body>
</html>''',
                variables=[
                    TemplateVariable("alert_type", "string", "アラートタイプ", required=True),
                    TemplateVariable("message", "string", "アラートメッセージ", required=True),
                    TemplateVariable("priority", "string", "優先度", required=True),
                    TemplateVariable("urgency", "string", "緊急度", required=True),
                    TemplateVariable("details", "object", "詳細情報", required=False),
                    TemplateVariable("recommendations", "array", "推奨アクション", required=False),
                    TemplateVariable("timestamp", "datetime", "アラート時刻", required=True),
                    TemplateVariable("priority_color", "string", "優先度カラー", default_value="#ff5722")
                ]
            ),
            
            # Webhook テンプレート
            NotificationTemplate(
                id="webhook_generic",
                name="汎用 Webhook",
                description="汎用Webhook通知テンプレート",
                template_type=TemplateType.WEBHOOK,
                template_format=TemplateFormat.JSON,
                content='''{
  "notification": {
    "id": "{{ notification_id }}",
    "type": "{{ notification_type }}",
    "priority": "{{ priority }}",
    "urgency": "{{ urgency }}",
    "timestamp": "{{ timestamp|format_datetime('%Y-%m-%dT%H:%M:%S.%fZ') }}",
    "source": "PRISM",
    "version": "2.0.0"
  },
  "data": {
    {% if title %}"title": "{{ title }}",{% endif %}
    {% if message %}"message": "{{ message }}",{% endif %}
    {% if content %}"content": "{{ content }}",{% endif %}
    {% if status %}"status": "{{ status }}",{% endif %}
    {% if due_date %}"due_date": "{{ due_date|format_datetime('%Y-%m-%dT%H:%M:%S.%fZ') }}",{% endif %}
    {% if metadata %}"metadata": {{ metadata|tojson }}{% endif %}
  },
  "user": {
    "id": "{{ user_id }}",
    "preferences": {{ user_preferences|tojson }}
  }
}''',
                variables=[
                    TemplateVariable("notification_id", "string", "通知ID", required=True),
                    TemplateVariable("notification_type", "string", "通知タイプ", required=True),
                    TemplateVariable("priority", "string", "優先度", required=True),
                    TemplateVariable("urgency", "string", "緊急度", required=True),
                    TemplateVariable("timestamp", "datetime", "通知時刻", required=True),
                    TemplateVariable("user_id", "string", "ユーザーID", required=True),
                    TemplateVariable("user_preferences", "object", "ユーザー設定", required=False),
                    TemplateVariable("title", "string", "タイトル", required=False),
                    TemplateVariable("message", "string", "メッセージ", required=False),
                    TemplateVariable("content", "string", "内容", required=False),
                    TemplateVariable("status", "string", "ステータス", required=False),
                    TemplateVariable("due_date", "datetime", "期日", required=False),
                    TemplateVariable("metadata", "object", "メタデータ", required=False)
                ]
            )
        ]
        
        for template in default_templates:
            self.templates[template.id] = template
    
    def add_template(self, template: NotificationTemplate):
        """テンプレートを追加"""
        with self.lock:
            template.updated_at = datetime.now()
            self.templates[template.id] = template
            logger.info(f"Added notification template: {template.name}")
    
    def update_template(self, template_id: str, updates: Dict[str, Any]):
        """テンプレートを更新"""
        with self.lock:
            if template_id in self.templates:
                template = self.templates[template_id]
                for key, value in updates.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                template.updated_at = datetime.now()
                logger.info(f"Updated notification template: {template_id}")
            else:
                logger.warning(f"Template not found: {template_id}")
    
    def remove_template(self, template_id: str):
        """テンプレートを削除"""
        with self.lock:
            if template_id in self.templates:
                del self.templates[template_id]
                logger.info(f"Removed notification template: {template_id}")
            else:
                logger.warning(f"Template not found: {template_id}")
    
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """テンプレートを取得"""
        with self.lock:
            return self.templates.get(template_id)
    
    def get_templates_by_type(self, template_type: TemplateType) -> List[NotificationTemplate]:
        """タイプ別テンプレート一覧を取得"""
        with self.lock:
            return [t for t in self.templates.values() if t.template_type == template_type and t.enabled]
    
    def render_notification(self, template_id: str, variables: Dict[str, Any]) -> Optional[str]:
        """通知をレンダリング"""
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None
        
        # 変数の検証
        missing_vars = []
        for var in template.variables:
            if var.required and var.name not in variables:
                missing_vars.append(var.name)
        
        if missing_vars:
            logger.error(f"Missing required variables: {missing_vars}")
            return None
        
        # デフォルト値の設定
        for var in template.variables:
            if var.name not in variables and var.default_value is not None:
                variables[var.name] = var.default_value
        
        # テンプレートレンダリング
        try:
            rendered_content = self.template_engine.render_template(template.content, variables)
            
            # JSONテンプレートの場合はパースして再フォーマット
            if template.template_format == TemplateFormat.JSON:
                try:
                    parsed_json = json.loads(rendered_content)
                    rendered_content = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON template parsing error: {e}")
                    return None
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return None
    
    def validate_template(self, template_content: str, template_format: TemplateFormat) -> Tuple[bool, str]:
        """テンプレートの検証"""
        try:
            # 基本的なテンプレート構文チェック
            self.template_engine.env.from_string(template_content)
            
            # フォーマット別の検証
            if template_format == TemplateFormat.JSON:
                # JSONテンプレートの場合は変数をダミー値で置換してテスト
                test_variables = {
                    "title": "Test Title",
                    "message": "Test Message",
                    "timestamp": datetime.now(),
                    "priority": "medium",
                    "urgency": "medium"
                }
                test_content = self.template_engine.render_template(template_content, test_variables)
                json.loads(test_content)
            
            return True, "Template is valid"
            
        except Exception as e:
            return False, f"Template validation error: {e}"
    
    def get_template_variables(self, template_id: str) -> List[Dict[str, Any]]:
        """テンプレート変数一覧を取得"""
        template = self.get_template(template_id)
        if not template:
            return []
        
        return [
            {
                "name": var.name,
                "type": var.type,
                "description": var.description,
                "default_value": var.default_value,
                "required": var.required,
                "validation_pattern": var.validation_pattern
            }
            for var in template.variables
        ]
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """全テンプレート一覧を取得"""
        with self.lock:
            return [
                {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "template_type": template.template_type.value,
                    "template_format": template.template_format.value,
                    "variables_count": len(template.variables),
                    "enabled": template.enabled,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat()
                }
                for template in self.templates.values()
            ]

# グローバルインスタンス
template_manager = NotificationTemplateManager()

def main():
    """テスト用メイン関数"""
    # テスト変数
    test_variables = {
        "title": "重要なタスク",
        "content": "これは重要なタスクの詳細です。",
        "due_date": datetime.now(),
        "status": "進行中",
        "priority": "high",
        "urgency": "medium",
        "timestamp": datetime.now()
    }
    
    # Slackテンプレートのテスト
    slack_result = template_manager.render_notification("slack_task_reminder", test_variables)
    print("Slack Template Result:")
    print(slack_result)
    
    # テンプレート一覧の表示
    templates = template_manager.get_all_templates()
    print(f"Available templates: {len(templates)}")

if __name__ == "__main__":
    main()
