# PRISM 導入手順書

## 📋 概要

PRISMは、Notionに入力されたデータをChatGPTで「Task／知識／Note」に自動分類・仕訳し、自然言語で問い合わせ可能なToDo／習慣／知識ベースへ整理するシステムです。

## 🎯 システム要件

### 必須要件
- **Docker**: 20.10以上
- **Docker Compose**: 2.0以上
- **Git**: 2.0以上
- **メモリ**: 4GB以上
- **ディスク**: 2GB以上の空き容量

### 推奨要件
- **OS**: macOS 12+, Ubuntu 20.04+, Windows 10+
- **CPU**: 2コア以上
- **メモリ**: 8GB以上

## 🚀 インストール手順

### Step 1: リポジトリのクローン

```bash
# リポジトリをクローン
git clone <repository-url>
cd PRISM

# プロジェクト構造の確認
ls -la
```

### Step 2: 環境変数の設定

```bash
# 環境変数ファイルを作成
cp deploy/env.example deploy/.env

# .env ファイルを編集
nano deploy/.env
```

**設定例:**
```bash
# PRISM 環境変数
PRISM_ENV=development
API_KEY=prism-dev-key-2025
OPENAI_API_KEY=sk-your-openai-key-here
NOTION_API_KEY=your_notion_api_key_here_key_here
MCP_BASE_URL=http://localhost:8081

# ログ設定
LOG_LEVEL=INFO
LOG_HUMAN=1

# Worker設定
WORKER_INTERVAL=60
```

### Step 3: サービスの起動

```bash
# deploy ディレクトリに移動
cd deploy

# サービスを起動
docker-compose up -d

# 起動状況を確認
docker-compose ps
```

### Step 4: 動作確認

```bash
# ヘルスチェック
curl http://localhost:8060/healthz

# Web UI アクセス
open http://localhost:8061
```

## 🔧 設定詳細

### ポート設定

| サービス | 外部ポート | 内部ポート | 説明 |
|---------|-----------|-----------|------|
| API | 8060 | 8000 | FastAPI サーバー |
| Web | 8061 | 80 | Nginx 静的配信 |
| Worker | - | - | バックグラウンド処理 |

### 環境変数詳細

| 変数名 | 必須 | デフォルト | 説明 |
|-------|------|-----------|------|
| `PRISM_ENV` | No | development | 実行環境 |
| `API_KEY` | Yes | - | API認証キー |
| `OPENAI_API_KEY` | No | - | OpenAI API キー |
| `NOTION_API_KEY` | No | - | Notion API キー |
| `MCP_BASE_URL` | No | - | MCP サーバー URL |
| `LOG_LEVEL` | No | INFO | ログレベル |
| `LOG_HUMAN` | No | 1 | 人間可読ログ |
| `WORKER_INTERVAL` | No | 60 | Worker実行間隔(秒) |

## 📊 使用方法

### Web UI での操作

1. **ブラウザでアクセス**: http://localhost:8061
2. **分類テスト**:
   - タイトル: "Task: submit report"
   - 本文: "deadline tomorrow"
   - 「Classify」ボタンをクリック
3. **検索テスト**:
   - キーワード: "report"
   - タイプ: "Task"
   - 「Search」ボタンをクリック

### API での操作

#### 分類API
```bash
curl -X POST http://localhost:8060/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: prism-dev-key-2025" \
  -d '{
    "items": [
      {
        "title": "Task: submit report",
        "body": "deadline tomorrow",
        "tags": []
      }
    ]
  }'
```

#### 検索API
```bash
curl "http://localhost:8060/query?q=report&type=Task"
```

#### ヘルスチェック
```bash
curl http://localhost:8060/healthz
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. ポート競合エラー
```
Error: Bind for 0.0.0.0:8060 failed: port is already allocated
```

**解決方法:**
```bash
# 使用中のポートを確認
lsof -i :8060
lsof -i :8061

# docker-compose.yml でポートを変更
# 例: 8060 → 9060, 8061 → 9061
```

#### 2. API キーエラー
```
{"error": {"code": "unauthorized", "message": "Invalid API key"}}
```

**解決方法:**
```bash
# .env ファイルの API_KEY を確認
cat deploy/.env | grep API_KEY

# リクエストヘッダーに正しいキーを設定
curl -H "X-API-Key: prism-dev-key-2025" http://localhost:8060/healthz
```

#### 3. コンテナ起動失敗
```
Container deploy-api-1 exited with code 1
```

**解決方法:**
```bash
# ログを確認
docker-compose logs api

# コンテナを再ビルド
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Worker の import エラー
```
ModuleNotFoundError: No module named 'src'
```

**解決方法:**
```bash
# Worker は現在開発中、API/Web は正常動作
# Worker を無効化する場合
# docker-compose.yml の worker セクションをコメントアウト
```

### ログ確認方法

```bash
# 全サービスのログ
docker-compose logs

# 特定サービスのログ
docker-compose logs api
docker-compose logs web
docker-compose logs worker

# コンテナ名で直接ログ確認
docker logs PRISM-API
docker logs PRISM-WEB
docker logs PRISM-WORKER

# リアルタイムログ
docker-compose logs -f api
docker logs -f PRISM-API
```

## 🛠️ 開発者向け情報

### プロジェクト構造
```
PRISM/
├── deploy/                 # デプロイ設定
│   ├── docker-compose.yml # Docker Compose設定
│   ├── .env               # 環境変数
│   └── env.example        # 環境変数テンプレート
├── docker/                # Dockerfile
├── src/                   # ソースコード
│   ├── api/              # FastAPI アプリ
│   ├── worker/           # バックグラウンドワーカー
│   └── web/              # 静的Webファイル
├── config/               # 設定ファイル
├── tests/                # テストファイル
└── README.md            # プロジェクト説明
```

### プラグイン開発

新しい分類ロジックを追加:

1. `src/api/plugins/custom_classifier.py` を作成
2. `register()` と `classify()` 関数を実装
3. 自動的にプラグインが読み込まれる

### テスト実行

```bash
# コンテナ内でテスト
docker-compose exec api pytest

# ローカルでテスト
cd src
python -m pytest ../tests/
```

## 📞 サポート

### 問題報告
- GitHub Issues で問題を報告
- ログファイルとエラーメッセージを含める

### ドキュメント
- README.md: 基本的な使用方法
- この導入手順書: 詳細なセットアップ手順
- API ドキュメント: http://localhost:8060/docs (Swagger UI)

## 🔄 アップデート手順

```bash
# 最新版を取得
git pull origin main

# コンテナを再ビルド
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 動作確認
curl http://localhost:8060/healthz
```

---

**最終更新**: 2025-10-21  
**バージョン**: v1.0.0
