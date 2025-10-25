# PRISM API リファレンス

**バージョン**: 2.0.0  
**ベースURL**: `http://localhost:8060`  
**更新日**: 2025年1月27日

---

## 目次

1. [認証](#1-認証)
2. [エンドポイント一覧](#2-エンドポイント一覧)
3. [詳細仕様](#3-詳細仕様)
4. [非同期処理](#4-非同期処理)
5. [メトリクス・監視](#5-メトリクス監視)
6. [エラーハンドリング](#6-エラーハンドリング)
7. [サンプルコード](#7-サンプルコード)

---

## 1. 認証

### 1.1 認証方式

PRISMは**APIキー認証**を使用します。

### 1.2 認証ヘッダー

```http
X-API-Key: your-api-key-here
```

### 1.3 APIキーの取得

APIキーは `.env` ファイルで設定します：

```bash
API_KEY=your-secret-key
```

### 1.4 認証エラー

認証に失敗した場合、以下のレスポンスが返されます：

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

---

## 2. エンドポイント一覧

| メソッド | エンドポイント | 認証 | 説明 |
|---------|--------------|------|------|
| GET | `/healthz` | 不要 | ヘルスチェック |
| POST | `/classify` | 必要 | アイテム分類 |
| GET | `/query` | 必要 | 検索 |
| POST | `/sync/notion` | 必要 | Notion同期トリガー |

---

## 3. 詳細仕様

### 3.1 GET /healthz

システムの健全性を確認します。

#### リクエスト

```http
GET /healthz HTTP/1.1
Host: localhost:8060
```

#### レスポンス

**成功時 (200 OK)**:
```json
{
  "status": "ok"
}
```

#### 例

```bash
curl http://localhost:8060/healthz
```

---

### 3.2 POST /classify

アイテムを分類します。

#### リクエスト

```http
POST /classify HTTP/1.1
Host: localhost:8060
Content-Type: application/json
X-API-Key: your-api-key

{
  "items": [
    {
      "title": "string (required)",
      "body": "string (optional)",
      "properties": {},
      "tags": []
    }
  ]
}
```

#### リクエストボディ

##### BatchRequest

| フィールド | 型 | 必須 | 説明 |
|-----------|---|------|------|
| items | Array<ItemModel> | ✅ | 分類対象アイテムの配列 |

##### ItemModel

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|---|------|----------|------|
| title | string | ✅ | - | タイトル |
| body | string | ❌ | null | 本文 |
| properties | object | ❌ | {} | Notionプロパティ |
| tags | Array<string> | ❌ | [] | タグリスト |

#### レスポンス

**成功時 (200 OK)**:
```json
{
  "results": [
    {
      "type": "Task",
      "score": 0.9,
      "tags": ["task"],
      "reason": "keyword match"
    }
  ]
}
```

##### 分類結果

| フィールド | 型 | 説明 |
|-----------|---|------|
| type | string | カテゴリ ("Task", "Knowledge", "Note") |
| score | number | 信頼度スコア (0.0 ~ 1.0) |
| tags | Array<string> | タグリスト |
| reason | string | 分類理由 |

**エラー時 (401 Unauthorized)**:
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

**エラー時 (422 Unprocessable Entity)**:
```json
{
  "detail": [
    {
      "loc": ["body", "items", 0, "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 例

**単一アイテムの分類**:
```bash
curl -X POST http://localhost:8060/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "items": [
      {
        "title": "レポート提出",
        "body": "明日までに提出する必要がある"
      }
    ]
  }'
```

**複数アイテムの分類**:
```bash
curl -X POST http://localhost:8060/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "items": [
      {
        "title": "Todo: ミーティング",
        "body": "来週の予定"
      },
      {
        "title": "Dockerの使い方",
        "body": "コンテナ技術の解説"
      },
      {
        "title": "今日の気づき",
        "body": "プロジェクトでの学び"
      }
    ]
  }'
```

**レスポンス**:
```json
{
  "results": [
    {
      "type": "Task",
      "score": 0.9,
      "tags": ["task"],
      "reason": "keyword match"
    },
    {
      "type": "Knowledge",
      "score": 0.85,
      "tags": ["knowledge", "docker"],
      "reason": "keyword match"
    },
    {
      "type": "Note",
      "score": 0.8,
      "tags": ["note"],
      "reason": "note keyword match"
    }
  ]
}
```

---

### 3.3 GET /query

データを検索します。

#### リクエスト

```http
GET /query?q=<query>&type=<type>&tag=<tag> HTTP/1.1
Host: localhost:8060
X-API-Key: your-api-key
```

#### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|---|------|------|---|
| q | string | ✅ | 検索クエリ | "Docker" |
| type | string | ❌ | タイプフィルタ | "Task", "Knowledge", "Note" |
| tag | string | ❌ | タグフィルタ | "docker" |

#### レスポンス

**成功時 (200 OK)**:
```json
{
  "query": "Docker",
  "results": [
    {
      "title": "Dockerの使い方",
      "body": "コンテナ技術の基本",
      "type": "Knowledge",
      "tags": ["knowledge", "docker"]
    }
  ]
}
```

#### 例

**基本検索**:
```bash
curl "http://localhost:8060/query?q=Docker" \
  -H "X-API-Key: your-api-key"
```

**タイプフィルタ付き**:
```bash
curl "http://localhost:8060/query?q=Docker&type=Knowledge" \
  -H "X-API-Key: your-api-key"
```

**タグフィルタ付き**:
```bash
curl "http://localhost:8060/query?q=Docker&tag=docker" \
  -H "X-API-Key: your-api-key"
```

---

### 3.4 POST /sync/notion

Notion同期を手動でトリガーします。

#### リクエスト

```http
POST /sync/notion HTTP/1.1
Host: localhost:8060
X-API-Key: your-api-key
```

#### レスポンス

**成功時 (200 OK)**:
```json
{
  "status": "queued"
}
```

#### 例

```bash
curl -X POST http://localhost:8060/sync/notion \
  -H "X-API-Key: your-api-key"
```

---

## 4. 非同期処理

### 4.1 非同期分類

大量のデータを効率的に処理するための非同期エンドポイントです。

#### 4.1.1 バッチ分類

```http
POST /async/classify/batch
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "items": [
    {
      "id": "item-1",
      "title": "重要な会議",
      "content": "来週のプロジェクト会議について"
    },
    {
      "id": "item-2", 
      "title": "買い物リスト",
      "content": "牛乳、パン、卵を買う"
    }
  ],
  "database_id": "your-database-id",
  "batch_size": 10
}
```

**レスポンス:**
```json
{
  "task_id": "uuid-task-id",
  "status": "processing",
  "message": "Classification started in background"
}
```

#### 4.1.2 INBOX処理

```http
POST /async/inbox/process
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "inbox_database_id": "inbox-db-id",
  "target_database_id": "target-db-id",
  "use_cache": true
}
```

#### 4.1.3 タスク状態確認

```http
GET /async/task/{task_id}
Authorization: Bearer your-api-key
```

**レスポンス:**
```json
{
  "task_id": "uuid-task-id",
  "status": "completed",
  "progress": 100,
  "total": 50,
  "results": [
    {
      "id": "item-1",
      "status": "classified",
      "category": "Task",
      "confidence": 0.95
    }
  ],
  "created_at": 1640995200.0,
  "completed_at": 1640995300.0
}
```

#### 4.1.4 アクティブタスク一覧

```http
GET /async/tasks
Authorization: Bearer your-api-key
```

#### 4.1.5 タスクキャンセル

```http
DELETE /async/task/{task_id}
Authorization: Bearer your-api-key
```

---

## 5. メトリクス・監視

### 5.1 Prometheusメトリクス

```http
GET /metrics
```

**レスポンス:** Prometheus形式のメトリクスデータ

### 5.2 メトリクスヘルスチェック

```http
GET /metrics/health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "uptime": 3600,
  "version": "2.0.0"
}
```

### 5.3 統計情報

```http
GET /metrics/stats
Authorization: Bearer your-api-key
```

**レスポンス:**
```json
{
  "system": {
    "memory": {
      "total": 8589934592,
      "used": 4294967296,
      "available": 4294967296,
      "percent": 50.0
    },
    "disk": {
      "total": 1000000000000,
      "used": 500000000000,
      "free": 500000000000,
      "percent": 50.0
    },
    "cpu": {
      "percent": 25.0,
      "count": 8
    }
  },
  "process": {
    "pid": 12345,
    "memory": {
      "rss": 1000000,
      "vms": 2000000
    },
    "cpu_percent": 10.0,
    "num_threads": 4,
    "create_time": 1640995200.0
  },
  "uptime": 3600
}
```

### 5.4 キャッシュ管理

#### 5.4.1 キャッシュクリア

```http
POST /async/cache/clear
Authorization: Bearer your-api-key
```

**レスポンス:**
```json
{
  "status": "success",
  "message": "All caches cleared"
}
```

---

## 6. エラーハンドリング

### 4.1 エラーレスポンス形式

```json
{
  "error": {
    "code": "string",
    "message": "string"
  }
}
```

### 4.2 HTTPステータスコード

| コード | 説明 | 例 |
|-------|------|---|
| 200 | OK | 正常処理 |
| 401 | Unauthorized | API Key不正 |
| 422 | Unprocessable Entity | バリデーションエラー |
| 500 | Internal Server Error | 内部エラー |

### 4.3 エラーコード一覧

| コード | 説明 | HTTPステータス |
|-------|------|---------------|
| unauthorized | 認証失敗 | 401 |
| validation_error | バリデーションエラー | 422 |
| internal_error | 内部エラー | 500 |

### 4.4 エラー例

#### 認証エラー
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

#### バリデーションエラー
```json
{
  "detail": [
    {
      "loc": ["body", "items"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 5. サンプルコード

### 5.1 cURLサンプル

#### 分類実行
```bash
#!/bin/bash
API_URL="http://localhost:8060"
API_KEY="your-api-key"

curl -X POST "$API_URL/classify" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "items": [
      {
        "title": "レポート提出",
        "body": "明日までに提出"
      }
    ]
  }' | jq '.'
```

### 5.2 Pythonサンプル

#### 基本的な使用例

```python
import requests
from typing import List, Dict

class PRISMClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def healthz(self) -> Dict:
        """ヘルスチェック"""
        response = requests.get(f"{self.base_url}/healthz")
        return response.json()
    
    def classify(self, items: List[Dict]) -> Dict:
        """アイテム分類"""
        response = requests.post(
            f"{self.base_url}/classify",
            headers=self.headers,
            json={"items": items}
        )
        response.raise_for_status()
        return response.json()
    
    def query(self, q: str, type: str = None, tag: str = None) -> Dict:
        """検索"""
        params = {"q": q}
        if type:
            params["type"] = type
        if tag:
            params["tag"] = tag
        
        response = requests.get(
            f"{self.base_url}/query",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def sync_notion(self) -> Dict:
        """Notion同期"""
        response = requests.post(
            f"{self.base_url}/sync/notion",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# 使用例
if __name__ == "__main__":
    client = PRISMClient(
        base_url="http://localhost:8060",
        api_key="your-api-key"
    )
    
    # ヘルスチェック
    health = client.healthz()
    print(f"Health: {health}")
    
    # 分類実行
    result = client.classify([
        {
            "title": "Docker学習",
            "body": "コンテナの使い方を学ぶ"
        }
    ])
    print(f"分類結果: {result['results'][0]['type']}")
    print(f"信頼度: {result['results'][0]['score']}")
    
    # 検索
    search_result = client.query(q="Docker", type="Knowledge")
    print(f"検索結果: {len(search_result['results'])}件")
```

### 5.3 JavaScriptサンプル

#### Fetch APIを使用

```javascript
class PRISMClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async healthz() {
    const response = await fetch(`${this.baseUrl}/healthz`);
    return response.json();
  }

  async classify(items) {
    const response = await fetch(`${this.baseUrl}/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({ items })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async query(q, type = null, tag = null) {
    const params = new URLSearchParams({ q });
    if (type) params.append('type', type);
    if (tag) params.append('tag', tag);

    const response = await fetch(`${this.baseUrl}/query?${params}`, {
      headers: {
        'X-API-Key': this.apiKey
      }
    });
    
    return response.json();
  }
}

// 使用例
const client = new PRISMClient('http://localhost:8060', 'your-api-key');

// 分類実行
client.classify([
  {
    title: 'Docker学習',
    body: 'コンテナの使い方を学ぶ'
  }
]).then(result => {
  console.log('分類結果:', result.results[0].type);
  console.log('信頼度:', result.results[0].score);
});

// 検索
client.query('Docker', 'Knowledge').then(result => {
  console.log('検索結果:', result.results.length, '件');
});
```

### 5.4 Node.jsサンプル (axios使用)

```javascript
const axios = require('axios');

class PRISMClient {
  constructor(baseUrl, apiKey) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      }
    });
  }

  async healthz() {
    const { data } = await this.client.get('/healthz');
    return data;
  }

  async classify(items) {
    const { data } = await this.client.post('/classify', { items });
    return data;
  }

  async query(q, type = null, tag = null) {
    const params = { q };
    if (type) params.type = type;
    if (tag) params.tag = tag;
    
    const { data } = await this.client.get('/query', { params });
    return data;
  }

  async syncNotion() {
    const { data } = await this.client.post('/sync/notion');
    return data;
  }
}

// 使用例
(async () => {
  const client = new PRISMClient('http://localhost:8060', 'your-api-key');
  
  try {
    // 分類実行
    const result = await client.classify([
      { title: 'タスク1', body: '明日までに提出' }
    ]);
    console.log('分類結果:', result.results[0]);
  } catch (error) {
    console.error('エラー:', error.message);
  }
})();
```

---

## 6. レート制限

現在、レート制限は設定されていません。将来的には実装予定です。

---

## 7. バージョニング

APIバージョンはURLパスには含まれていません。破壊的変更がある場合は、別途通知されます。

---

## 8. サポート

APIに関する質問や問題は、GitHubのIssueで報告してください。

---

**ドキュメント改訂履歴**

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-10-21 | 初版作成 | PRISM Team |







