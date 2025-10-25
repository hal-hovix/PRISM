# Notion MCPサーバー ガイド

## 概要

PRISMシステムはNotion MCPサーバーを提供し、ChatGPTからNotionデータベースへの問い合わせを可能にします。Model Context Protocol (MCP) に準拠したHTTP APIサーバーとして実装されており、ChatGPTやその他のMCPクライアントから利用できます。

## 機能

### 利用可能なツール

| ツール名 | 説明 | エンドポイント |
|---------|------|---------------|
| `search_databases` | Notionのデータベースを検索 | `GET /tools/search_databases` |
| `query_database` | 指定されたデータベースをクエリ | `POST /tools/query_database` |
| `get_page` | 指定されたページの詳細を取得 | `GET /tools/get_page/{page_id}` |
| `create_page` | 新しいページを作成 | `POST /tools/create_page` |
| `update_page` | 既存のページを更新 | `PUT /tools/update_page` |

### ChatGPT連携エンドポイント

- **`POST /chatgpt/query`**: ChatGPTからの問い合わせを処理

## セットアップ

### 1. 環境変数設定

`.env`ファイルに以下の設定が必要です：

```bash
# Notion API設定
NOTION_API_KEY=your_notion_api_key_here
```

### 2. Docker Compose起動

```bash
# MCPサーバーを起動
docker-compose up -d PRISM-MCP

# ヘルスチェック
curl http://localhost:8062/health
```

### 3. 動作確認

```bash
# 利用可能なツール一覧
curl http://localhost:8062/tools

# データベース検索テスト
curl http://localhost:8062/tools/search_databases
```

## ChatGPT連携方法

### 1. ChatGPT設定

ChatGPTでMCPサーバーを使用するには、以下の設定が必要です：

1. **サーバーURL**: `http://localhost:8062`
2. **認証**: 不要（ローカル環境）
3. **プロトコル**: HTTP REST API

### 2. 問い合わせ例

#### データベース検索
```json
{
  "type": "search_databases",
  "params": {}
}
```

#### データベースクエリ
```json
{
  "type": "query_database",
  "params": {
    "database_id": "2935fbef-07e2-808a-8d27-cfbc1a5fcf25",
    "filter": {
      "property": "カテゴリ",
      "select": {
        "equals": "技術"
      }
    }
  }
}
```

#### ページ取得
```json
{
  "type": "get_page",
  "params": {
    "page_id": "page-id-here"
  }
}
```

#### ページ作成
```json
{
  "type": "create_page",
  "params": {
    "parent": {
      "database_id": "2935fbef-07e2-808a-8d27-cfbc1a5fcf25"
    },
    "properties": {
      "タイトル": {
        "title": [{"text": {"content": "新しいページ"}}]
      },
      "カテゴリ": {
        "select": {"name": "技術"}
      }
    }
  }
}
```

## API リファレンス

### 基本エンドポイント

#### `GET /`
- **説明**: ルートエンドポイント
- **レスポンス**: サーバー情報

#### `GET /health`
- **説明**: ヘルスチェック
- **レスポンス**: 
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-10-24T08:19:55.243380"
  }
  ```

#### `GET /tools`
- **説明**: 利用可能なツール一覧
- **レスポンス**: ツール情報の配列

### ツールエンドポイント

#### `GET /tools/search_databases`
- **説明**: Notionのデータベースを検索
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": [/* データベース配列 */]
  }
  ```

#### `POST /tools/query_database`
- **説明**: データベースをクエリ
- **リクエストボディ**:
  ```json
  {
    "database_id": "database-id",
    "filter": {/* フィルター条件 */}
  }
  ```
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": [/* ページ配列 */]
  }
  ```

#### `GET /tools/get_page/{page_id}`
- **説明**: ページの詳細を取得
- **パラメータ**: `page_id` - ページID
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": {/* ページ情報 */}
  }
  ```

#### `POST /tools/create_page`
- **説明**: 新しいページを作成
- **リクエストボディ**:
  ```json
  {
    "parent": {
      "database_id": "database-id"
    },
    "properties": {/* プロパティ */}
  }
  ```
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": {/* 作成されたページ情報 */}
  }
  ```

#### `PUT /tools/update_page`
- **説明**: 既存のページを更新
- **リクエストボディ**:
  ```json
  {
    "page_id": "page-id",
    "properties": {/* 更新するプロパティ */}
  }
  ```
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": {/* 更新されたページ情報 */}
  }
  ```

### ChatGPT連携エンドポイント

#### `POST /chatgpt/query`
- **説明**: ChatGPTからの問い合わせを処理
- **リクエストボディ**:
  ```json
  {
    "type": "query_type",
    "params": {/* パラメータ */}
  }
  ```
- **レスポンス**: 
  ```json
  {
    "success": true,
    "type": "query_type",
    "data": {/* 結果データ */},
    "timestamp": "2025-10-24T08:19:55.243380"
  }
  ```

## 使用例

### 1. データベース一覧取得

```bash
curl -X GET http://localhost:8062/tools/search_databases
```

### 2. 特定のデータベースをクエリ

```bash
curl -X POST http://localhost:8062/tools/query_database \
  -H "Content-Type: application/json" \
  -d '{
    "database_id": "2935fbef-07e2-808a-8d27-cfbc1a5fcf25",
    "filter": {
      "property": "カテゴリ",
      "select": {
        "equals": "技術"
      }
    }
  }'
```

### 3. ChatGPT経由での問い合わせ

```bash
curl -X POST http://localhost:8062/chatgpt/query \
  -H "Content-Type: application/json" \
  -d '{
    "type": "search_databases",
    "params": {}
  }'
```

## トラブルシューティング

### よくある問題

#### 1. サーバーが起動しない
```bash
# ログを確認
docker logs PRISM-MCP

# 環境変数を確認
docker exec PRISM-MCP env | grep NOTION
```

#### 2. Notion API認証エラー
- `NOTION_API_KEY`が正しく設定されているか確認
- Notion APIキーが有効か確認
- データベースへのアクセス権限を確認

#### 3. データベースが見つからない
- データベースIDが正しいか確認
- データベースが削除されていないか確認
- アクセス権限を確認

### ログ確認

```bash
# コンテナログを確認
docker logs -f PRISM-MCP

# ヘルスチェック
curl http://localhost:8062/health
```

## セキュリティ

### 認証
- 現在はローカル環境での使用を想定
- 本番環境では適切な認証機構の実装を推奨

### データ保護
- Notion APIキーは環境変数で管理
- ローカル環境でのみ動作
- HTTPS通信の実装を推奨

## 制限事項

- Notion APIの利用制限に従う
- 大量のデータ処理時は時間がかかる場合があります
- リアルタイム同期は対応していません

## 関連ファイル

- `src/mcp_server/notion_mcp_server.py`: MCPプロトコル準拠サーバー
- `src/mcp_server/notion_mcp_http_server.py`: HTTP APIサーバー
- `docker/Dockerfile.mcp`: MCPサーバー用Dockerfile
- `docker-compose.yml`: Docker Compose設定

## 更新履歴

- **2025-10-24**: 初版作成
- **2025-10-24**: ChatGPT連携機能追加
- **2025-10-24**: HTTP APIサーバー実装
