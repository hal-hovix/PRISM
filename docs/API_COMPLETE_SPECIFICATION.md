# PRISM API 完全仕様書

## 概要

PRISM (Personalized Recommendation and Intelligent System for Management) は、Notionデータベースと連携した高度なタスク管理・自動分類システムです。本ドキュメントでは、PRISM API v2.0の完全な仕様を説明します。

## 基本情報

- **API バージョン**: 2.0.0
- **ベースURL**: `http://localhost:8060`
- **認証方式**: Bearer Token (API Key)
- **データ形式**: JSON
- **文字エンコーディング**: UTF-8

## 認証

すべてのAPIエンドポイント（`/healthz`を除く）は認証が必要です。

```http
Authorization: Bearer YOUR_API_KEY
```

## エンドポイント一覧

### 1. ヘルスチェック

#### GET /healthz
基本的なヘルスチェック

**レスポンス:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "service": "prism-api",
  "version": "1.0.0"
}
```

#### GET /healthz/detailed
詳細なヘルスチェック（認証必須）

**レスポンス:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "service": "prism-api",
  "version": "1.0.0",
  "system": {
    "memory_percent": 45.2,
    "disk_percent": 23.1,
    "cpu_percent": 12.5
  }
}
```

### 2. 自動分類

#### POST /classify
テキストの自動分類

**リクエスト:**
```json
{
  "text": "明日の会議の準備をする",
  "title": "会議準備"
}
```

**レスポンス:**
```json
{
  "status": "success",
  "classification": {
    "category": "Task",
    "confidence": 0.95,
    "suggested_database": "Task",
    "extracted_info": {
      "due_date": "2025-10-26",
      "priority": "medium"
    }
  }
}
```

### 3. データクエリ

#### GET /query/tasks
タスクの取得

**クエリパラメータ:**
- `limit`: 取得件数 (デフォルト: 100)
- `status`: ステータスフィルタ
- `priority`: 優先度フィルタ

**レスポンス:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "task_123",
      "title": "会議準備",
      "status": "In Progress",
      "priority": "High",
      "due_date": "2025-10-26",
      "created_at": "2025-10-25T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET /query/todos
ToDoの取得

#### GET /query/knowledge
ナレッジの取得

#### GET /query/notes
ノートの取得

#### GET /query/projects
プロジェクトの取得

#### GET /query/habits
習慣の取得

### 4. メトリクス

#### GET /metrics/
Prometheus形式のメトリクス

**レスポンス:**
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 8819.0
```

### 5. 非同期処理

#### GET /async/tasks
非同期タスクの状態確認

#### POST /async/process
非同期処理の開始

### 6. アナリティクス

#### GET /analytics/overview
システム概要の取得

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "total_tasks": 150,
    "completed_tasks": 120,
    "completion_rate": 0.8,
    "categories": {
      "Task": 100,
      "Note": 30,
      "Knowledge": 20
    }
  }
}
```

#### GET /analytics/trends
トレンド分析

#### GET /analytics/performance
パフォーマンス分析

### 7. セマンティック検索

#### POST /semantic-search
意味ベースの検索

**リクエスト:**
```json
{
  "query": "重要なプロジェクト",
  "limit": 10,
  "databases": ["Task", "Project"]
}
```

**レスポンス:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "proj_123",
      "title": "新製品開発",
      "relevance_score": 0.92,
      "database": "Project",
      "snippet": "重要な新製品開発プロジェクト..."
    }
  ]
}
```

### 8. AIアシスタント

#### POST /assistant/chat
AIチャット機能

**リクエスト:**
```json
{
  "message": "今日のタスクを教えて",
  "context": {
    "user_id": "user_123",
    "session_id": "session_456"
  }
}
```

**レスポンス:**
```json
{
  "status": "success",
  "response": "今日のタスクは以下の通りです：\n1. 会議準備\n2. レポート作成",
  "suggestions": [
    "タスクの優先順位を変更しますか？",
    "新しいタスクを追加しますか？"
  ]
}
```

### 9. 自動レポート

#### GET /auto-reports/weekly
週次レポートの生成

#### GET /auto-reports/monthly
月次レポートの生成

#### POST /auto-reports/custom
カスタムレポートの生成

### 10. 通知システム

#### GET /notifications/settings
通知設定の取得

**レスポンス:**
```json
{
  "status": "success",
  "settings": {
    "email_enabled": true,
    "slack_enabled": false,
    "task_reminders": true,
    "habit_notifications": true,
    "system_alerts": true
  }
}
```

#### PUT /notifications/settings
通知設定の更新

#### POST /notifications/test
通知テスト

#### GET /notifications/status
通知ステータスの確認

### 11. 高度な通知

#### GET /advanced-notifications/settings
高度な通知設定

#### POST /advanced-notifications/smart-filter
スマートフィルター設定

#### POST /advanced-notifications/template
通知テンプレート管理

#### GET /advanced-notifications/analytics
通知アナリティクス

#### POST /advanced-notifications/escalation
エスカレーション設定

### 12. パフォーマンス監視

#### GET /performance/metrics
パフォーマンスメトリクス

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "system": {
      "memory_usage_mb": 74.8,
      "memory_percent": 0.95,
      "cpu_percent": 0.0,
      "uptime_seconds": 17.5
    },
    "endpoints": {
      "health.healthz": {
        "request_count": 1,
        "avg_response_time": 0.000027,
        "min_response_time": 0.000027,
        "max_response_time": 0.000027
      }
    }
  }
}
```

#### GET /performance/report
パフォーマンスレポート

#### POST /performance/optimize
パフォーマンス最適化

#### GET /performance/health
パフォーマンスヘルスチェック

#### GET /performance/stats
パフォーマンス統計

### 13. セキュリティ

#### GET /security/summary
セキュリティサマリー

**レスポンス:**
```json
{
  "timestamp": "2025-10-25T14:12:39.562151",
  "summary": {
    "total_events_today": 2,
    "events_last_hour": 2,
    "active_alerts": 0,
    "blocked_clients": 0,
    "total_clients": 1
  },
  "event_breakdown": {
    "login_success": 2
  },
  "level_breakdown": {
    "low": 2
  }
}
```

#### GET /security/events
セキュリティイベント

#### GET /security/alerts
セキュリティアラート

#### POST /security/alerts/{alert_id}/resolve
アラート解決

#### GET /security/rate-limits
レート制限統計

#### POST /security/rate-limits/reset
レート制限リセット

#### POST /security/clients/action
クライアントアクション

#### POST /security/ips/action
IPアクション

#### POST /security/validate
入力検証

#### GET /security/health
セキュリティヘルスチェック

### 14. 監視・ログ

#### GET /monitoring/dashboard
監視ダッシュボード

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-10-25T14:17:12.662151",
    "health": {
      "overall_status": "healthy",
      "health_score": 85,
      "components": [
        {
          "name": "api",
          "status": "healthy",
          "message": "API is healthy",
          "response_time": 0.018
        }
      ]
    },
    "metrics": {
      "cpu_percent": 0.9,
      "memory_percent": 17.9,
      "disk_percent": 25.3,
      "process_count": 2,
      "uptime_hours": 23.6
    },
    "logs": {
      "total_entries_24h": 150,
      "error_rate": 2.5,
      "entries_by_level": {
        "INFO": 120,
        "WARNING": 25,
        "ERROR": 5
      }
    }
  }
}
```

#### GET /monitoring/health
システムヘルスチェック

#### POST /monitoring/health/check
指定コンポーネントのヘルスチェック

#### GET /monitoring/metrics
システムメトリクス

#### GET /monitoring/logs
ログ取得

#### POST /monitoring/logs/search
ログ検索

#### GET /monitoring/logs/stats
ログ統計

#### POST /monitoring/logs/export
ログエクスポート

#### POST /monitoring/logs/archive
ログアーカイブ

#### POST /monitoring/logs/cleanup
ログクリーンアップ

## エラーレスポンス

### 標準エラー形式

```json
{
  "detail": "エラーメッセージ",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-10-25T14:17:12.662151"
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `201 Created`: 作成成功
- `400 Bad Request`: リクエストエラー
- `401 Unauthorized`: 認証エラー
- `403 Forbidden`: アクセス拒否
- `404 Not Found`: リソースが見つからない
- `429 Too Many Requests`: レート制限超過
- `500 Internal Server Error`: サーバーエラー

### エラーコード一覧

- `INVALID_API_KEY`: 無効なAPIキー
- `RATE_LIMIT_EXCEEDED`: レート制限超過
- `VALIDATION_ERROR`: バリデーションエラー
- `NOTION_API_ERROR`: Notion API エラー
- `CLASSIFICATION_ERROR`: 分類エラー
- `DATABASE_ERROR`: データベースエラー
- `SECURITY_VIOLATION`: セキュリティ違反

## レート制限

- **基本制限**: 60リクエスト/分
- **バースト制限**: 10リクエスト/10秒
- **グローバル制限**: 600リクエスト/分

レート制限に達した場合、`429 Too Many Requests`が返されます。

## データベーススキーマ

### Task データベース
```json
{
  "title": "string",
  "status": "Not Started|In Progress|Completed",
  "priority": "Low|Medium|High|Urgent",
  "due_date": "YYYY-MM-DD",
  "assignee": "string",
  "tags": ["string"],
  "description": "string"
}
```

### ToDo データベース
```json
{
  "title": "string",
  "completed": "boolean",
  "due_date": "YYYY-MM-DD",
  "priority": "Low|Medium|High",
  "category": "string"
}
```

### Knowledge データベース
```json
{
  "title": "string",
  "content": "string",
  "category": "string",
  "tags": ["string"],
  "source": "string",
  "last_updated": "YYYY-MM-DD"
}
```

### Note データベース
```json
{
  "title": "string",
  "content": "string",
  "type": "Meeting|Personal|Work",
  "tags": ["string"],
  "created_date": "YYYY-MM-DD"
}
```

### Project データベース
```json
{
  "name": "string",
  "description": "string",
  "status": "Planning|Active|Completed|On Hold",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "team_members": ["string"]
}
```

### Habit データベース
```json
{
  "name": "string",
  "description": "string",
  "frequency": "Daily|Weekly|Monthly",
  "target": "number",
  "current_streak": "number",
  "last_completed": "YYYY-MM-DD"
}
```

## 環境変数

### 必須設定
- `NOTION_API_KEY`: Notion APIキー
- `OPENAI_API_KEY`: OpenAI APIキー
- `API_KEY`: PRISM APIキー

### オプション設定
- `WORKER_INTERVAL`: ワーカー実行間隔（秒）
- `GOOGLE_CALENDAR_ENABLED`: Google Calendar連携有効化
- `REPORT_EMAIL_ENABLED`: レポートメール有効化
- `SLACK_WEBHOOK_URL`: Slack Webhook URL
- `LOG_LEVEL`: ログレベル

## 使用例

### Python クライアント例

```python
import requests

# API設定
API_BASE_URL = "http://localhost:8060"
API_KEY = "your_api_key"
headers = {"Authorization": f"Bearer {API_KEY}"}

# テキスト分類
def classify_text(text, title=None):
    response = requests.post(
        f"{API_BASE_URL}/classify",
        json={"text": text, "title": title},
        headers=headers
    )
    return response.json()

# タスク取得
def get_tasks(limit=100):
    response = requests.get(
        f"{API_BASE_URL}/query/tasks",
        params={"limit": limit},
        headers=headers
    )
    return response.json()

# セマンティック検索
def semantic_search(query, databases=None):
    response = requests.post(
        f"{API_BASE_URL}/semantic-search",
        json={"query": query, "databases": databases},
        headers=headers
    )
    return response.json()
```

### JavaScript クライアント例

```javascript
const API_BASE_URL = 'http://localhost:8060';
const API_KEY = 'your_api_key';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// テキスト分類
async function classifyText(text, title = null) {
  const response = await fetch(`${API_BASE_URL}/classify`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ text, title })
  });
  return await response.json();
}

// タスク取得
async function getTasks(limit = 100) {
  const response = await fetch(`${API_BASE_URL}/query/tasks?limit=${limit}`, {
    headers
  });
  return await response.json();
}

// セマンティック検索
async function semanticSearch(query, databases = null) {
  const response = await fetch(`${API_BASE_URL}/semantic-search`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, databases })
  });
  return await response.json();
}
```

## 更新履歴

### v2.0.0 (2025-10-25)
- セキュリティ強化（レート制限、入力検証、監視）
- パフォーマンス最適化
- 高度な通知システム
- 包括的な監視・ログ機能
- AIアシスタント機能
- セマンティック検索
- 自動レポート生成

### v1.0.0 (2025-10-20)
- 基本的な分類機能
- Notion連携
- 基本的なクエリ機能
