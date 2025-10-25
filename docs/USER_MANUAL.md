# PRISM 操作マニュアル

**バージョン**: 1.0.0  
**作成日**: 2025年10月21日  
**対象ユーザー**: エンドユーザー

---

## 目次

1. [はじめに](#1-はじめに)
2. [初期セットアップ](#2-初期セットアップ)
3. [基本操作](#3-基本操作)
4. [Web UI操作](#4-web-ui操作)
5. [API操作](#5-api操作)
6. [トラブルシューティング](#6-トラブルシューティング)

---

## 1. はじめに

### 1.1 PRISMとは

PRISMは、Notionに入力したデータを自動的に「Task（タスク）」「Knowledge（知識）」「Note（メモ）」に分類し、整理するシステムです。

### 1.2 主な機能

- ✅ **自動分類**: タイトルと本文から自動的にカテゴリ分類
- 🔍 **検索機能**: 自然言語での検索
- 🔄 **自動同期**: Notionとの定期同期（60秒間隔）
- 📊 **CSV保存**: 分類結果をCSV形式で保存

### 1.3 必要なもの

- Docker & Docker Compose
- Notion API キー（オプション）
- OpenAI API キー（オプション）

---

## 2. 初期セットアップ

### 2.1 インストール

#### ステップ1: リポジトリのクローン

```bash
git clone <repository-url>
cd PRISM
```

#### ステップ2: 環境変数の設定

```bash
# サンプルファイルをコピー
cp env.example .env

# エディタで編集
nano .env
```

**設定例**:
```bash
# API認証キー（お好みの値に変更）
API_KEY=my-secret-api-key

# OpenAI API キー（必要な場合）
OPENAI_API_KEY=sk-your-openai-key-here

# Notion API キー（必要な場合）
NOTION_API_KEY=your_notion_api_key_here_key_here
```

#### ステップ3: システム起動

```bash
# サービスを起動
docker-compose up -d

# 起動確認
docker-compose ps
```

**正常起動時の表示**:
```
NAME           STATUS                   PORTS
PRISM-API      Up (healthy)            0.0.0.0:8060->8000/tcp
PRISM-WEB      Up                      0.0.0.0:8061->80/tcp
PRISM-WORKER   Up
```

#### ステップ4: 動作確認

ブラウザで以下にアクセス:
- **Web UI**: http://localhost:8061
- **ヘルスチェック**: http://localhost:8060/healthz

---

## 3. 基本操作

### 3.1 システムの起動・停止

#### 起動
```bash
cd PRISM
docker-compose up -d
```

#### 停止
```bash
docker-compose down
```

#### 再起動
```bash
docker-compose restart
```

#### ログ確認
```bash
# 全コンテナのログ
docker-compose logs

# 特定コンテナのログ
docker-compose logs PRISM-API

# リアルタイムでログ表示
docker-compose logs -f
```

### 3.2 設定変更

#### 環境変数の変更

1. `.env` ファイルを編集
2. コンテナを再起動

```bash
# .envを編集
nano .env

# 再起動
docker-compose restart
```

#### 同期間隔の変更

`.env` に以下を追加:
```bash
WORKER_INTERVAL=120  # 120秒（2分）間隔
```

---

## 4. Web UI操作

### 4.1 Web UIへのアクセス

ブラウザで http://localhost:8061 を開く

### 4.2 分類の実行

#### ステップ1: タイトルと本文を入力

```
タイトル: レポート提出
本文: 明日までにレポートを提出する
```

#### ステップ2: 「分類する」ボタンをクリック

#### ステップ3: 結果を確認

```
分類結果:
タイプ: Task
信頼度: 0.9
タグ: task
理由: keyword match
```

### 4.3 検索の実行

#### ステップ1: 検索ボックスに入力

```
検索キーワード: Docker
```

#### ステップ2: フィルタを選択（オプション）

- タイプ: Knowledge
- タグ: docker

#### ステップ3: 「検索」ボタンをクリック

---

## 5. API操作

### 5.1 curlコマンドでの操作

#### 5.1.1 ヘルスチェック

```bash
curl http://localhost:8060/healthz
```

**レスポンス**:
```json
{
  "status": "ok"
}
```

#### 5.1.2 分類実行

```bash
curl -X POST http://localhost:8060/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "items": [
      {
        "title": "レポート提出",
        "body": "明日までに提出"
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
    }
  ]
}
```

#### 5.1.3 検索

```bash
curl "http://localhost:8060/query?q=Docker&type=Knowledge" \
  -H "X-API-Key: your-api-key"
```

#### 5.1.4 Notion同期トリガー

```bash
curl -X POST http://localhost:8060/sync/notion \
  -H "X-API-Key: your-api-key"
```

### 5.2 Pythonスクリプトでの操作

```python
import requests

API_URL = "http://localhost:8060"
API_KEY = "your-api-key"

# 分類実行
response = requests.post(
    f"{API_URL}/classify",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    json={
        "items": [
            {
                "title": "Docker学習",
                "body": "コンテナの使い方を学ぶ"
            }
        ]
    }
)

result = response.json()
print(f"分類結果: {result['results'][0]['type']}")
print(f"信頼度: {result['results'][0]['score']}")
```

---

## 6. トラブルシューティング

### 6.1 コンテナが起動しない

#### 症状
```bash
docker-compose ps
# STATUS列が "Exited" になっている
```

#### 対処法

**ステップ1: ログを確認**
```bash
docker-compose logs PRISM-API
```

**ステップ2: ポートの競合を確認**
```bash
# ポート8060, 8061が使用中か確認
lsof -i :8060
lsof -i :8061
```

**ステップ3: ポート変更（必要な場合）**

`docker-compose.yml` を編集:
```yaml
ports:
  - "8070:8000"  # 8060 → 8070 に変更
```

**ステップ4: 再起動**
```bash
docker-compose down
docker-compose up -d
```

### 6.2 分類結果がおかしい

#### 症状
- Taskなのに Noteと分類される
- Knowledgeなのに Taskと分類される

#### 対処法

**方法1: キーワードを追加する**

タイトルや本文に明示的なキーワードを含める:

| カテゴリ | 推奨キーワード |
|---------|--------------|
| Task | todo, タスク, 締切, 期限, 提出, やること |
| Knowledge | 使い方, 設計, 技術, 解説, 手順, how to |
| Note | メモ, 気づき, 日記, 備忘録, 記録 |

**方法2: プラグインの調整**

`src/api/plugins/` 配下のプラグインファイルを編集し、キーワードやスコアを調整する。

### 6.3 APIが401エラーを返す

#### 症状
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid API key"
  }
}
```

#### 対処法

**X-API-Keyヘッダーを確認**:
```bash
# .envファイルのAPI_KEYを確認
cat .env | grep API_KEY

# curlコマンドのヘッダーを確認
curl -X POST http://localhost:8060/classify \
  -H "X-API-Key: changeme-api-key" \  # ← この値を.envと一致させる
  ...
```

### 6.4 Web UIが表示されない

#### 症状
- http://localhost:8061 にアクセスできない
- "Connection refused" エラー

#### 対処法

**ステップ1: コンテナ状態を確認**
```bash
docker-compose ps
# PRISM-WEB が Up になっているか確認
```

**ステップ2: ログを確認**
```bash
docker-compose logs PRISM-WEB
```

**ステップ3: 再起動**
```bash
docker-compose restart PRISM-WEB
```

### 6.5 Notion同期が動かない

#### 症状
- Workerが動作していない
- CSVファイルが更新されない

#### 対処法

**ステップ1: Worker状態を確認**
```bash
docker-compose logs PRISM-WORKER
```

**ステップ2: 環境変数を確認**
```bash
# .envファイルを確認
cat .env | grep -E "(NOTION_API_KEY|MCP_BASE_URL)"
```

**ステップ3: 手動同期をトリガー**
```bash
curl -X POST http://localhost:8060/sync/notion \
  -H "X-API-Key: your-api-key"
```

### 6.6 よくある質問（FAQ）

#### Q1: 複数のアイテムを一度に分類できますか？

**A**: はい、`items` 配列に複数のアイテムを含めることができます。

```json
{
  "items": [
    {"title": "アイテム1", "body": "..."},
    {"title": "アイテム2", "body": "..."},
    {"title": "アイテム3", "body": "..."}
  ]
}
```

#### Q2: 分類結果のCSVはどこに保存されますか？

**A**: `NoyionDB_CSV/` フォルダに保存されます。

```
NoyionDB_CSV/
├── Task.csv
├── Knowledge.csv
└── Note.csv
```

#### Q3: 自分でプラグインを追加できますか？

**A**: はい、`src/api/plugins/` に新しい `.py` ファイルを追加すれば自動検出されます。詳細は開発者ガイドを参照してください。

#### Q4: OpenAI APIは必須ですか？

**A**: いいえ、キーワードベースの分類はOpenAI APIなしでも動作します。`template_plugin` を使わない場合は不要です。

#### Q5: データはどこに保存されますか？

**A**: 現在はCSV形式でローカルに保存されます。将来的にはデータベース対応も予定されています。

---

## 7. 活用例

### 7.1 日次タスク管理

**朝**: Notionにその日のタスクを入力  
**自動**: PRISMが自動的にTask分類  
**確認**: `NoyionDB_CSV/Task.csv` で一覧確認

### 7.2 技術メモの整理

**学習中**: 技術メモをNotionに入力  
**自動**: PRISMがKnowledge分類  
**検索**: 後で "Docker" などで検索

### 7.3 日記・振り返り

**夜**: その日の気づきをNotionに入力  
**自動**: PRISMがNote分類  
**蓄積**: `NoyionDB_CSV/Note.csv` に蓄積

---

## 8. 次のステップ

### より詳しく学ぶには

- 📖 [セットアップガイド](SETUP_GUIDE.md) - 詳細な導入手順
- 🏗️ [詳細設計書](DESIGN.md) - システムアーキテクチャ
- 📋 [要件定義書](REQUIREMENTS.md) - 機能仕様
- 💻 [API リファレンス](API_REFERENCE.md) - API詳細仕様

### サポート

問題が解決しない場合は、GitHubのIssueで報告してください。

---

**ドキュメント改訂履歴**

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-10-21 | 初版作成 | PRISM Team |







