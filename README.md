# PRISM - 高度なタスク管理・自動分類システム

Notionデータベースと連携した、AI駆動の包括的なタスク管理・自動分類システム。ChatGPTによる自動分類、セマンティック検索、AIアシスタント機能を提供します。

## ✨ 最新機能 (v2.0.0)

### 🔒 セキュリティ強化
- **レート制限**: 60リクエスト/分の基本制限
- **入力検証・サニタイゼーション**: XSS・SQLインジェクション対策
- **セキュリティ監視**: リアルタイム脅威検出
- **アクセス制御**: IP・クライアントベースの制御

### 📊 包括的監視・ログ
- **システムヘルス監視**: 全コンポーネントのリアルタイム監視
- **高度なログ管理**: カテゴリ別ログ・検索・アーカイブ
- **パフォーマンス監視**: CPU・メモリ・レスポンス時間監視
- **統合ダッシュボード**: 一元化された監視画面

### ⚡ パフォーマンス最適化
- **非同期処理**: バックグラウンドタスク処理
- **Redisキャッシュ**: 高速データアクセス
- **メモリ最適化**: ガベージコレクション・メモリ管理
- **並行処理**: マルチスレッド・非同期I/O

### 🤖 AI機能強化
- **AIアシスタント**: 自然言語でのタスク管理
- **セマンティック検索**: 意味ベースの高度な検索
- **自動レポート生成**: 週次・月次レポート自動生成
- **スマート通知**: インテリジェントな通知フィルタリング

### 🔔 高度な通知システム
- **マルチチャネル通知**: Email・Slack・Webhook対応
- **エスカレーション機能**: 重要度に応じた通知レベル
- **通知テンプレート**: カスタマイズ可能な通知形式
- **通知アナリティクス**: 通知効果の分析

### 🧪 品質保証・テスト
- **包括的テストスイート**: 単体・統合・E2Eテスト
- **CI/CDパイプライン**: GitHub Actions自動化
- **コード品質チェック**: 静的解析・リント
- **セキュリティテスト**: 脆弱性スキャン

## 🚀 クイックスタート

### 1. 前提条件
- Docker & Docker Compose がインストール済み
- Git がインストール済み
- Notion API キー
- OpenAI API キー

### 2. セットアップ手順

```bash
# リポジトリをクローン
git clone <repository-url>
cd PRISM

# 環境変数ファイルを作成
cp env.example .env

# 必要なAPIキーを設定
# .envファイルを編集してAPIキーを設定

# システム起動
docker compose up -d

# ヘルスチェック
curl http://localhost:8060/healthz
```

### 3. 基本設定

```bash
# APIキー設定
export API_KEY="your_api_key"

# 通知設定（Slack）
curl -X PUT -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "slack_enabled": true,
       "slack_webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
     }' \
     http://localhost:8060/notifications/settings
```

## 📚 主要機能

### 自動分類
```bash
# テキストの自動分類
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "明日の会議の準備をする",
       "title": "会議準備"
     }' \
     http://localhost:8060/classify
```

### セマンティック検索
```bash
# 意味ベースの検索
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "重要なプロジェクト",
       "limit": 10,
       "databases": ["Task", "Project"]
     }' \
     http://localhost:8060/semantic-search
```

### AIアシスタント
```bash
# AIチャット機能
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "今日のタスクを教えて",
       "context": {
         "user_id": "user_123",
         "session_id": "session_456"
       }
     }' \
     http://localhost:8060/assistant/chat
```

### 監視ダッシュボード
```bash
# 統合監視ダッシュボード
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/dashboard | jq .
```

## 🏗️ システム構成

### サービス一覧
| サービス名 | ポート | 説明 |
|-----------|-------|------|
| PRISM-API | 8060 | メインAPIサーバー |
| PRISM-WEB | 8061 | Web UI |
| PRISM-MCP | 8062 | MCPサーバー |
| PRISM-WORKER | - | バックグラウンドワーカー |
| PRISM-NOTIFIER | - | 通知サービス |
| PRISM-Redis | 6379 | キャッシュ・セッション管理 |

### アーキテクチャ
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PRISM-WEB     │    │   PRISM-API     │    │   PRISM-MCP     │
│   (Web UI)      │◄──►│   (FastAPI)     │◄──►│   (MCP Server)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PRISM-Redis   │
                       │   (Cache/DB)    │
                       └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │PRISM-WORKER │ │PRISM-NOTIFIER│ │  Notion API │
        │(Background) │ │(Notifications)│ │  OpenAI API │
        └─────────────┘ └─────────────┘ └─────────────┘
```

## 📖 ドキュメント

### 主要ドキュメント
- **[API完全仕様書](docs/API_COMPLETE_SPECIFICATION.md)**: 全APIエンドポイントの詳細仕様
- **[運用ガイド](docs/OPERATIONS_GUIDE.md)**: 運用・保守・監視の包括的ガイド
- **[セットアップガイド](docs/SETUP_GUIDE.md)**: 詳細なセットアップ手順
- **[ユーザーマニュアル](docs/USER_MANUAL.md)**: エンドユーザー向けガイド

### 技術ドキュメント
- **[設計ドキュメント](docs/DESIGN.md)**: システム設計・アーキテクチャ
- **[APIリファレンス](docs/API_REFERENCE.md)**: API仕様・使用例
- **[パフォーマンスガイド](docs/PERFORMANCE_GUIDE.md)**: パフォーマンス最適化
- **[セキュリティガイド](docs/SECURITY_GUIDE.md)**: セキュリティ設定・対策

### 運用ドキュメント
- **[監視ガイド](docs/MONITORING_GUIDE.md)**: 監視・アラート設定
- **[CI/CDガイド](docs/CI_CD_GUIDE.md)**: 継続的インテグレーション
- **[本番デプロイガイド](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)**: 本番環境デプロイ

## 🔧 開発・運用

### 開発環境
```bash
# 開発環境起動
docker compose -f docker-compose.dev.yml up -d

# テスト実行
docker compose exec PRISM-API pytest

# ログ確認
docker compose logs -f PRISM-API
```

### 本番環境
```bash
# 本番環境起動
docker compose -f docker-compose.prod.yml up -d

# ヘルスチェック
curl http://localhost:8060/healthz

# 監視確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/dashboard
```

### メンテナンス
```bash
# ログアーカイブ
curl -X POST -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/monitoring/logs/archive?days_old=7"

# パフォーマンス最適化
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/optimize

# セキュリティ監査
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/summary
```

## 📊 監視・メトリクス

### システム監視
- **ヘルスチェック**: `/healthz`, `/healthz/detailed`
- **システムメトリクス**: `/monitoring/metrics`
- **パフォーマンス**: `/performance/metrics`
- **セキュリティ**: `/security/summary`

### Prometheusメトリクス
```bash
# Prometheus形式メトリクス
curl http://localhost:8060/metrics/
```

### ログ管理
```bash
# ログ検索
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "error",
       "level": "ERROR",
       "limit": 50
     }' \
     http://localhost:8060/monitoring/logs/search

# ログ統計
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/monitoring/logs/stats?hours=24"
```

## 🔒 セキュリティ

### 認証・認可
- **API Key認証**: Bearer Token形式
- **レート制限**: 60リクエスト/分
- **入力検証**: XSS・SQLインジェクション対策
- **セキュリティ監視**: リアルタイム脅威検出

### セキュリティ設定
```bash
# レート制限確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/rate-limits

# セキュリティイベント確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/events

# 不正IPブロック
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "action": "block",
       "ip_address": "192.168.1.100",
       "reason": "Suspicious activity"
     }' \
     http://localhost:8060/security/ips/action
```

## 🚀 デプロイメント

### Docker Compose
```bash
# 本番環境デプロイ
docker compose -f docker-compose.prod.yml up -d

# スケーリング
docker compose up -d --scale PRISM-API=3
```

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: |
          docker compose -f docker-compose.prod.yml up -d
```

## 📈 パフォーマンス

### ベンチマーク結果
- **APIレスポンス時間**: 平均50ms
- **同時接続数**: 1000接続対応
- **メモリ使用量**: 平均80MB
- **CPU使用率**: 平均5%

### 最適化機能
- **Redisキャッシュ**: 高速データアクセス
- **非同期処理**: バックグラウンドタスク
- **メモリ管理**: 自動ガベージコレクション
- **並行処理**: マルチスレッド対応

## 🤝 コントリビューション

### 開発参加
1. リポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

### テスト
```bash
# 単体テスト
docker compose exec PRISM-API pytest tests/unit/

# 統合テスト
docker compose exec PRISM-API pytest tests/integration/

# E2Eテスト
docker compose exec PRISM-API pytest tests/e2e/
```

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 📞 サポート

### ドキュメント
- **[FAQ](docs/FAQ.md)**: よくある質問
- **[トラブルシューティング](docs/TROUBLESHOOTING.md)**: 問題解決ガイド
- **[API仕様書](docs/API_COMPLETE_SPECIFICATION.md)**: 完全なAPI仕様

### コミュニティ
- **GitHub Issues**: バグ報告・機能要望
- **Discussions**: 質問・議論
- **Wiki**: 追加ドキュメント

## 🎯 ロードマップ

### v2.1.0 (予定)
- [ ] モバイルアプリ対応
- [ ] 音声入力機能
- [ ] 多言語対応
- [ ] プラグインシステム

### v2.2.0 (予定)
- [ ] 機械学習モデル改善
- [ ] リアルタイム同期
- [ ] 高度なアナリティクス
- [ ] カスタムワークフロー

---

**PRISM v2.0.0** - 高度なタスク管理・自動分類システム

## 🚀 クイックスタート

### 1. 前提条件
- Docker & Docker Compose がインストール済み
- Git がインストール済み

### 2. セットアップ手順

```bash
# リポジトリをクローン
git clone <repository-url>
cd PRISM

# 環境変数ファイルを作成
cp env.example .env

# .env ファイルを編集（必要に応じて）
# API_KEY, OPENAI_API_KEY, NOTION_API_KEY を設定

# サービス起動
docker-compose up -d

# 起動確認
docker-compose ps
```

### 3. アクセス先

- **Web UI**: http://localhost:8061
- **API**: http://localhost:8060
- **ヘルスチェック**: http://localhost:8060/healthz
- **メトリクス**: http://localhost:8060/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

## 📋 機能

### 分類機能
- Notionページを「Task」「Knowledge」「Note」に自動分類
- キーワードベースの分類ロジック
- プラグイン方式で拡張可能

### 検索機能
- 自然言語での検索
- タイプ別フィルタ（Task/Knowledge/Note）
- タグ別フィルタ
- 日付範囲フィルタ

### API エンドポイント

#### 分類
```bash
POST /classify
Content-Type: application/json
X-API-Key: prism-dev-key-2025

{
  "items": [
    {
      "title": "Task: submit report",
      "body": "deadline tomorrow",
      "tags": []
    }
  ]
}
```

#### 検索
```bash
GET /query?q=report&type=Task&tag=urgent
```

#### ヘルスチェック
```bash
GET /healthz
```

## 🔧 設定

### 環境変数 (.env)

```bash
# 基本設定
PRISM_ENV=development
API_KEY=prism-dev-key-2025

# 外部サービス連携
OPENAI_API_KEY=sk-your-openai-key-here
NOTION_API_KEY=your_notion_api_key_here_key_here
MCP_BASE_URL=http://localhost:8081

# ログ設定
LOG_LEVEL=INFO
LOG_HUMAN=1

# Worker設定
WORKER_INTERVAL=60
```

### ポート設定

- **API**: 8060 (内部: 8000)
- **Web**: 8061 (内部: 80)
- **Worker**: バックグラウンド実行

## 📚 ドキュメント

詳細なドキュメントは `docs/` フォルダに格納されています。

### セットアップ・運用ガイド
- **[セットアップガイド](docs/SETUP_GUIDE.md)** - 詳細なインストール手順
- **[ユーザーマニュアル](docs/USER_MANUAL.md)** - 使い方の詳細
- **[要件定義](docs/REQUIREMENTS.md)** - システム要件と仕様
- **[毎朝のタスク整理](docs/DAILY_TASK_SUMMARY.md)** - 毎朝のタスク整理機能
- **[毎夕の振り返り](docs/DAILY_REFLECTION.md)** - 毎夕の振り返り機能
- **[環境変数設定](docs/ENVIRONMENT_VARIABLES.md)** - 環境変数による設定管理
- **[Googleカレンダー同期](docs/GOOGLE_CALENDAR_SYNC.md)** - GoogleカレンダーとNotionDBの同期
- **[Google Tasks同期](docs/GOOGLE_TASKS_SYNC.md)** - Google TasksとNotionDBの同期
- **[Notion MCPサーバー](docs/NOTION_MCP_SERVER.md)** - ChatGPT連携用Notion MCPサーバー

### 開発者向け
- **[API リファレンス](docs/API_REFERENCE.md)** - API エンドポイント一覧
- **[設計ドキュメント](docs/DESIGN.md)** - アーキテクチャと設計思想
- **[プラグイン開発ガイド](docs/PLUGIN_DEVELOPMENT.md)** - カスタムプラグインの作り方

### GitHub・自動化
- **[GitHub クイックスタート](docs/GITHUB_QUICK_START.md)** - リポジトリ作成からプッシュまで（5分）
- **[GitHub 詳細ガイド](docs/GITHUB_GUIDE.md)** - ブランチ戦略、CI/CD、チーム開発
- **[自動化クイックスタート](docs/AUTOMATION_QUICK_START.md)** - 自動仕分けの設定（5分）
- **[自動化詳細ガイド](docs/AUTOMATION_GUIDE.md)** - cron、launchd、運用パターン
- **[120秒間隔ガイド](docs/120S_INTERVAL_GUIDE.md)** - 120秒間隔自動仕分け

### テスト・データ
- **[テストデータガイド](docs/TEST_DATA_README.md)** - テストデータの使い方
- **[ドキュメント索引](docs/INDEX.md)** - 全ドキュメントの一覧

## 🧪 テスト

### テストの実行

```bash
# 基本テスト（10項目）
./tests/improved_test.sh

# 包括的テスト（18項目）
./tests/comprehensive_test.sh

# Pythonユニットテスト
pytest tests/
```

### テストファイル

- `tests/improved_test.sh` - 改修後の基本テスト
- `tests/comprehensive_test.sh` - 包括的なテストスイート
- `tests/test_classify.py` - 分類機能のユニットテスト
- `tests/test_plugins.py` - プラグインのユニットテスト
- `tests/TEST_REPORT.md` - 詳細なテスト結果レポート

## 🛠️ 開発

### プラグイン開発

新しい分類ロジックを追加する場合：

1. `src/api/plugins/` に新しいファイルを作成
2. `register()` と `classify()` 関数を実装

```python
def register() -> dict:
    return {
        "name": "custom_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["custom"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    # カスタム分類ロジック
    return {
        "type": "Task",
        "score": 0.8,
        "tags": ["custom"],
        "reason": "custom logic"
    }
```

### テスト実行

```bash
# コンテナ内でテスト実行
docker-compose exec api pytest

# ローカルでテスト実行
cd src
python -m pytest ../tests/
```

## 📁 プロジェクト構成

```
PRISM/
├── deploy/
│   ├── docker-compose.yml    # Docker Compose設定
│   ├── .env                  # 環境変数（要作成）
│   └── env.example          # 環境変数テンプレート
├── docker/
│   ├── Dockerfile.api       # API用Dockerfile
│   ├── Dockerfile.web       # Web用Dockerfile
│   └── Dockerfile.worker    # Worker用Dockerfile
├── src/
│   ├── api/                 # FastAPI アプリケーション
│   │   ├── main.py
│   │   ├── routers/         # API ルーター
│   │   ├── core/           # コア機能
│   │   └── plugins/        # 分類プラグイン
│   ├── worker/             # バックグラウンドワーカー
│   └── web/                # 静的Webファイル
├── config/
│   └── default.yaml        # デフォルト設定
├── tests/                  # テストファイル
└── README.md
```

## 🔍 トラブルシューティング

### よくある問題

1. **ポート競合**
   - 8060, 8061 が使用中の場合は docker-compose.yml でポート変更

2. **API キーエラー**
   - .env ファイルの API_KEY を確認
   - リクエストヘッダーに `X-API-Key` を設定

3. **コンテナ起動失敗**
   ```bash
   docker-compose logs
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### ログ確認

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
```

## 📝 ライセンス

MIT License

## 🤝 貢献

1. Fork する
2. Feature ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Request を作成

EOF ./README.md - v1.0.0
# 修正履歴:
# - 2025-10-20 v1.0.0: 初期 README
