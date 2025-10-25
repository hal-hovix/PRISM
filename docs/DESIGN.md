# PRISM システム詳細設計書

**バージョン**: 1.1.0  
**作成日**: 2025年10月21日  
**最終更新**: 2025年10月21日

---

## 1. システムアーキテクチャ

### 1.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                       外部サービス                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Notion   │  │ OpenAI   │  │   MCP    │              │
│  │   API    │  │   API    │  │  Server  │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
└───────┼─────────────┼─────────────┼────────────────────┘
        │             │             │
        │             │             │
┌───────┼─────────────┼─────────────┼────────────────────┐
│       │             │             │                     │
│  ┌────▼─────────────▼─────────────▼────┐                │
│  │        PRISM-API (FastAPI)          │  Port: 8060   │
│  │  ┌──────────┐  ┌──────────────┐    │                │
│  │  │  Router  │  │    Core      │    │                │
│  │  │          │  │  - Plugins   │    │                │
│  │  │/classify │  │  - LLM Client│    │                │
│  │  │/query    │  │  - MCP Client│    │                │
│  │  │/healthz  │  │  - Notion    │    │                │
│  │  └──────────┘  └──────────────┘    │                │
│  └─────────────────────────────────────┘                │
│           │                                              │
│  ┌────────▼──────────────────────────┐                  │
│  │   PRISM-WORKER (Background)       │                  │
│  │   - Notion Sync (60s interval)    │                  │
│  │   - CSV Export                    │                  │
│  └───────────────────────────────────┘                  │
│                                                          │
│  ┌─────────────────────────────────┐                    │
│  │   PRISM-WEB (Nginx)             │  Port: 8061       │
│  │   - index.html                  │                    │
│  │   - app.js                      │                    │
│  │   - styles.css                  │                    │
│  └─────────────────────────────────┘                    │
│                                                          │
│  ┌─────────────────────────────────┐                    │
│  │   NoyionDB_CSV/                 │                    │
│  │   - Task.csv                    │                    │
│  │   - Knowledge.csv               │                    │
│  │   - Note.csv                    │                    │
│  └─────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

### 1.2 コンポーネント構成

#### 1.2.1 PRISM-API
- **役割**: RESTful APIの提供
- **技術**: FastAPI + Uvicorn
- **ポート**: 8060 (外部) → 8000 (内部)
- **責務**:
  - 分類処理のオーケストレーション
  - プラグイン管理
  - API認証

#### 1.2.2 PRISM-WORKER
- **役割**: バックグラウンド同期処理
- **技術**: Python 3.11+
- **実行間隔**: 60秒（設定可能）
- **責務**:
  - Notionからのデータ取得
  - CSV形式でのデータ保存

#### 1.2.3 PRISM-WEB
- **役割**: Web UI提供
- **技術**: Nginx + HTML/JS
- **ポート**: 8061 (外部) → 80 (内部)
- **責務**:
  - ユーザーインターフェース
  - API呼び出し

---

## 2. データ設計

### 2.1 データモデル

#### 2.1.1 入力データ（ItemModel）
```python
class ItemModel(BaseModel):
    title: str                          # タイトル（必須）
    body: Optional[str] = None          # 本文
    properties: Dict[str, Any] = {}     # Notionプロパティ
    tags: List[str] = []                # タグリスト
```

#### 2.1.2 分類結果
```python
{
    "type": str,        # "Task" | "Knowledge" | "Note"
    "score": float,     # 0.0 ~ 1.0
    "tags": List[str],  # タグリスト
    "reason": str       # 分類理由
}
```

### 2.2 CSV形式

#### 2.2.1 Task.csv
```csv
id,title,body,deadline,status,tags,created_at,updated_at
1,レポート提出,明日までに提出,2025-10-22,pending,"task,urgent",2025-10-21,2025-10-21
```

#### 2.2.2 Knowledge.csv
```csv
id,title,body,category,tags,created_at,updated_at
1,Dockerの使い方,コンテナ技術の基本,tech,"knowledge,docker",2025-10-21,2025-10-21
```

#### 2.2.3 Note.csv
```csv
id,title,body,tags,created_at,updated_at
1,今日の気づき,プロジェクトでの学び,"note,learning",2025-10-21,2025-10-21
```

---

## 3. API設計

### 3.1 エンドポイント仕様

#### 3.1.1 GET /healthz
**概要**: ヘルスチェック

**リクエスト**: なし

**レスポンス**:
```json
{
  "status": "ok"
}
```

**ステータスコード**:
- 200 OK: 正常

---

#### 3.1.2 POST /classify
**概要**: アイテム分類

**認証**: X-API-Key ヘッダー必須

**リクエスト**:
```json
{
  "items": [
    {
      "title": "レポート提出",
      "body": "明日までに提出する",
      "tags": []
    }
  ]
}
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
    }
  ]
}
```

**ステータスコード**:
- 200 OK: 成功
- 401 Unauthorized: 認証失敗
- 422 Unprocessable Entity: バリデーションエラー

---

#### 3.1.3 GET /query
**概要**: 検索

**認証**: X-API-Key ヘッダー必須

**クエリパラメータ**:
- `q`: 検索クエリ（必須）
- `type`: タイプフィルタ（オプション: Task/Knowledge/Note）
- `tag`: タグフィルタ（オプション）

**レスポンス**:
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

**ステータスコード**:
- 200 OK: 成功
- 401 Unauthorized: 認証失敗

---

#### 3.1.4 POST /sync/notion
**概要**: Notion同期トリガー

**認証**: X-API-Key ヘッダー必須

**リクエスト**: なし

**レスポンス**:
```json
{
  "status": "queued"
}
```

**ステータスコード**:
- 200 OK: 成功
- 401 Unauthorized: 認証失敗

---

## 4. プラグイン設計

### 4.1 プラグインインターフェース

#### 4.1.1 register()
```python
def register() -> dict:
    """
    プラグインのメタデータを返す
    
    Returns:
        dict: {
            "name": str,              # プラグイン名
            "version": str,           # バージョン（例: "v1.0.0"）
            "capabilities": List[str], # 機能リスト（例: ["classify"]）
            "labels": List[str]       # ラベル（例: ["task", "knowledge"]）
        }
    """
```

#### 4.1.2 classify()
```python
def classify(item: dict, *, llm, notion, config) -> dict:
    """
    アイテムを分類する
    
    Args:
        item: 分類対象アイテム（ItemModel.model_dump()の結果）
        llm: LLMクライアント
        notion: Notionクライアント
        config: 設定オブジェクト
    
    Returns:
        dict: {
            "type": str,      # "Task" | "Knowledge" | "Note"
            "score": float,   # 0.0 ~ 1.0
            "tags": List[str],
            "reason": str
        }
    """
```

### 4.2 プラグイン優先順位

分類は**最高スコア選択方式**を採用：

```python
best = {"type": "Note", "score": 0.0, "tags": [], "reason": "default"}
for plugin in plugins.values():
    result = plugin.module.classify(item, llm=llm, notion=notion, config=config)
    if result.get("score", 0.0) > best.get("score", 0.0):
        best = result
return best
```

### 4.3 標準プラグイン

#### 4.3.1 task_classifier.py
- **バージョン**: v1.1.0
- **スコア**: キーワード一致時 0.9、不一致時 0.2
- **キーワード**: todo, task, deadline, タスク, 締切, 期限 など

#### 4.3.2 knowledge_classifier.py
- **バージョン**: v1.1.0
- **スコア**: キーワード一致時 0.85、不一致時 0.2
- **キーワード**: how to, architecture, 設計, 知識, 技術 など

#### 4.3.3 note_classifier.py
- **バージョン**: v1.1.0
- **スコア**: キーワード一致時 0.8、不一致時 0.6
- **キーワード**: メモ, 気づき, 日記, 備忘録 など

#### 4.3.4 template_plugin.py
- **バージョン**: v1.1.0
- **スコア**: 0.5（フォールバック）
- **ロジック**: LLMによる分類

---

## 5. 処理フロー

### 5.1 分類処理フロー

```
クライアント
    │
    ▼
POST /classify
    │
    ▼
認証チェック (X-API-Key)
    │
    ▼
バリデーション (Pydantic)
    │
    ▼
プラグイン検出
    │
    ▼
各プラグインで分類実行
    │  ├─ task_classifier (score: 0.9 or 0.2)
    │  ├─ knowledge_classifier (score: 0.85 or 0.2)
    │  ├─ note_classifier (score: 0.8 or 0.6)
    │  └─ template_plugin (score: 0.5)
    │
    ▼
最高スコア選択
    │
    ▼
結果返却
    │
    ▼
クライアント
```

### 5.2 同期処理フロー

```
PRISM-WORKER
    │
    ▼
60秒待機
    │
    ▼
MCP/Notion からページ取得
    │
    ▼
各ページを分類
    │
    ▼
カテゴリ別にグループ化
    │
    ▼
CSV保存
    │  ├─ NoyionDB_CSV/Task.csv
    │  ├─ NoyionDB_CSV/Knowledge.csv
    │  └─ NoyionDB_CSV/Note.csv
    │
    ▼
ログ出力
    │
    ▼
60秒待機（繰り返し）
```

---

## 6. エラーハンドリング

### 6.1 エラー種類

#### 6.1.1 認証エラー
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

#### 6.1.2 バリデーションエラー
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

#### 6.1.3 内部エラー
```json
{
  "error": {
    "code": "internal_error",
    "message": "An internal error occurred"
  }
}
```

### 6.2 リトライロジック

- **外部API呼び出し**: 3回までリトライ（指数バックオフ）
- **Notion同期**: エラー時は次の同期サイクルで再試行
- **分類処理**: 1プラグイン失敗でも他プラグインは継続

---

## 7. 設定管理

### 7.1 環境変数

```bash
# 環境設定
PRISM_ENV=production

# 認証
API_KEY=changeme-api-key

# 外部サービス
OPENAI_API_KEY=sk-your-openai-key
NOTION_API_KEY=your_notion_api_key_here_key
MCP_BASE_URL=http://mcp-server:8063

# ログ設定
LOG_LEVEL=INFO
LOG_HUMAN=1

# Worker設定
WORKER_INTERVAL=60
```

### 7.2 設定ファイル (config/default.yaml)

```yaml
app_name: "PRISM API"
version: "1.0.0"

log:
  level: "INFO"
  human_readable: true

plugins:
  directory: "src/api/plugins"
  auto_discover: true

classification:
  default_category: "Note"
  min_confidence: 0.5

sync:
  interval_seconds: 60
  batch_size: 100
```

---

## 8. セキュリティ設計

### 8.1 認証
- API Key認証（X-API-Keyヘッダー）
- 環境変数での管理
- ハードコード禁止

### 8.2 データ保護
- 機密情報は環境変数
- .gitignoreで除外
- ログにPII情報を含めない

### 8.3 通信
- コンテナ間通信はDocker内部ネットワーク
- 外部公開はAPIとWebのみ

---

## 9. パフォーマンス設計

### 9.1 目標値
- ヘルスチェック: 100ms以内
- 分類処理: 2秒以内（1アイテム）
- 検索処理: 1秒以内

### 9.2 最適化ポイント
- プラグイン並列実行（将来）
- CSVキャッシュ（将来）
- 非同期I/O活用

---

## 10. 監視・ログ

### 10.1 ヘルスチェック
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### 10.2 ログ形式

#### JSON形式
```json
{
  "timestamp": "2025-10-21T12:00:00Z",
  "level": "INFO",
  "message": "Classification completed",
  "context": {
    "type": "Task",
    "score": 0.9
  }
}
```

#### ヒューマンリーダブル形式
```
2025-10-21 12:00:00 [INFO] Classification completed: type=Task, score=0.9
```

---

## 11. テスト設計

### 11.1 ユニットテスト
- プラグインの個別テスト
- APIエンドポイントのテスト
- バリデーションロジックのテスト

### 11.2 統合テスト
- API → プラグイン → レスポンスの一連のフロー
- Worker → CSV保存の一連のフロー

### 11.3 E2Eテスト
- Web UI → API → 分類 → 結果表示
- シェルスクリプトによる自動テスト

---

## 12. デプロイ設計

### 12.1 コンテナ構成
```yaml
services:
  PRISM-API:
    image: prism-api:latest
    ports: ["8060:8000"]
    
  PRISM-WEB:
    image: prism-web:latest
    ports: ["8061:80"]
    
  PRISM-WORKER:
    image: prism-worker:latest
```

### 12.2 ボリューム
```yaml
volumes:
  - ./config:/app/config:ro      # 設定ファイル（読み取り専用）
  - ./NoyionDB_CSV:/app/data:rw  # CSVデータ（読み書き）
```

---

## 13. 拡張ポイント

### 13.1 新規プラグイン追加
1. `src/api/plugins/` に新ファイル作成
2. `register()` と `classify()` を実装
3. 自動検出される（再起動不要）

### 13.2 データストア変更
- CSV → SQLite/PostgreSQL への移行
- `src/api/core/storage.py` の実装

### 13.3 認証方式変更
- OAuth 2.0対応
- JWT認証対応

---

**文書履歴**

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-10-21 | 初版作成 | PRISM Team |
| 1.1.0 | 2025-10-21 | プラグインバージョン更新反映 | PRISM Team |







