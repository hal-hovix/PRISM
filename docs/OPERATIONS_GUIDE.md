# PRISM 運用ガイド

## 概要

本ドキュメントでは、PRISMシステムの運用・保守・監視に関する包括的なガイドを提供します。

## システム構成

### サービス一覧

| サービス名 | ポート | 説明 | 依存関係 |
|-----------|-------|------|----------|
| PRISM-API | 8060 | メインAPIサーバー | Redis |
| PRISM-WEB | 8061 | Web UI | PRISM-API |
| PRISM-MCP | 8062 | MCPサーバー | PRISM-API |
| PRISM-WORKER | - | バックグラウンドワーカー | Redis, Notion API |
| PRISM-NOTIFIER | - | 通知サービス | PRISM-API |
| PRISM-Redis | 6379 | キャッシュ・セッション管理 | - |

### Docker Compose構成

```yaml
services:
  PRISM-API:
    image: prism-api:latest
    ports:
      - "8060:8000"
    environment:
      - API_KEY=${API_KEY}
      - NOTION_API_KEY=${NOTION_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - PRISM-Redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 日常運用

### 1. システム起動

```bash
# 全サービス起動
docker compose up -d

# 特定サービス起動
docker compose up -d PRISM-API PRISM-WEB

# 起動確認
docker compose ps
```

### 2. ヘルスチェック

#### 基本ヘルスチェック
```bash
# API基本ヘルス
curl http://localhost:8060/healthz

# 詳細ヘルスチェック（認証必要）
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/healthz/detailed
```

#### 監視ダッシュボード
```bash
# 統合監視ダッシュボード
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/dashboard | jq .
```

### 3. ログ監視

#### リアルタイムログ確認
```bash
# 全サービスログ
docker compose logs -f

# 特定サービスログ
docker compose logs -f PRISM-API

# エラーログのみ
docker compose logs --tail=100 PRISM-API | grep ERROR
```

#### ログ統計確認
```bash
# 過去24時間のログ統計
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/monitoring/logs/stats?hours=24" | jq .
```

### 4. パフォーマンス監視

#### システムメトリクス
```bash
# システムメトリクス取得
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/metrics | jq .

# パフォーマンスレポート
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/report | jq .
```

#### Prometheusメトリクス
```bash
# Prometheus形式メトリクス
curl http://localhost:8060/metrics/
```

## トラブルシューティング

### 1. よくある問題と解決方法

#### API接続エラー
**症状**: `Connection refused` エラー
**原因**: APIサーバーが起動していない
**解決方法**:
```bash
# サービス状態確認
docker compose ps

# APIサーバー再起動
docker compose restart PRISM-API

# ログ確認
docker compose logs PRISM-API
```

#### 認証エラー
**症状**: `Invalid API key` エラー
**原因**: APIキーが無効または設定されていない
**解決方法**:
```bash
# 環境変数確認
echo $API_KEY

# .envファイル確認
cat .env | grep API_KEY

# APIキー再設定
export API_KEY="your_api_key"
```

#### Notion API接続エラー
**症状**: `Notion API error` エラー
**原因**: Notion APIキーが無効またはレート制限
**解決方法**:
```bash
# Notion APIキー確認
echo $NOTION_API_KEY

# APIキー再設定
export NOTION_API_KEY="your_notion_api_key"

# レート制限確認
curl -H "Authorization: Bearer $NOTION_API_KEY" \
     https://api.notion.com/v1/users/me
```

#### Redis接続エラー
**症状**: `Redis connection failed` エラー
**原因**: Redisサーバーが起動していない
**解決方法**:
```bash
# Redis状態確認
docker compose ps PRISM-Redis

# Redis再起動
docker compose restart PRISM-Redis

# Redis接続テスト
docker exec -it PRISM-Redis redis-cli ping
```

### 2. パフォーマンス問題

#### 高CPU使用率
**症状**: CPU使用率が80%以上
**原因**: 重い処理や無限ループ
**解決方法**:
```bash
# プロセス確認
docker stats

# パフォーマンスメトリクス確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/metrics | jq .

# 最適化実行
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/optimize
```

#### 高メモリ使用率
**症状**: メモリ使用率が90%以上
**原因**: メモリリークまたは大量データ処理
**解決方法**:
```bash
# メモリ使用量確認
docker stats

# ガベージコレクション実行
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/optimize

# サービス再起動
docker compose restart PRISM-API
```

#### レスポンス時間の遅延
**症状**: APIレスポンス時間が5秒以上
**原因**: データベース接続問題または重い処理
**解決方法**:
```bash
# レスポンス時間確認
curl -w "@curl-format.txt" -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/healthz/detailed

# パフォーマンス統計確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/stats | jq .
```

### 3. セキュリティ問題

#### レート制限エラー
**症状**: `Rate limit exceeded` エラー
**原因**: API呼び出し頻度が制限を超過
**解決方法**:
```bash
# レート制限統計確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/rate-limits | jq .

# レート制限リセット
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/rate-limits/reset
```

#### セキュリティアラート
**症状**: セキュリティアラートが発生
**原因**: 不正なアクセス試行またはセキュリティ違反
**解決方法**:
```bash
# セキュリティイベント確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/events | jq .

# アクティブアラート確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/alerts | jq .
```

## 定期メンテナンス

### 1. 日次メンテナンス

#### ログローテーション
```bash
# 古いログのアーカイブ
curl -X POST -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/monitoring/logs/archive?days_old=7"

# アーカイブログのクリーンアップ
curl -X POST -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/monitoring/logs/cleanup?days_old=30"
```

#### システムヘルスチェック
```bash
# 包括的ヘルスチェック
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/health | jq .

# システムメトリクス確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/metrics | jq .
```

### 2. 週次メンテナンス

#### パフォーマンス最適化
```bash
# パフォーマンス最適化実行
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/optimize

# 最適化結果確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/report | jq .
```

#### セキュリティ監査
```bash
# セキュリティサマリー確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/summary | jq .

# セキュリティイベント確認
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/security/events?limit=100" | jq .
```

### 3. 月次メンテナンス

#### データベース最適化
```bash
# Redis メモリ使用量確認
docker exec -it PRISM-Redis redis-cli info memory

# Redis メモリ最適化
docker exec -it PRISM-Redis redis-cli memory purge
```

#### システム更新
```bash
# Dockerイメージ更新
docker compose pull

# サービス再起動
docker compose up -d

# 更新確認
docker compose ps
```

## 監視・アラート

### 1. 監視項目

#### システムリソース
- CPU使用率（警告: 80%, 緊急: 95%）
- メモリ使用率（警告: 85%, 緊急: 95%）
- ディスク使用率（警告: 85%, 緊急: 95%）
- ネットワークI/O

#### アプリケーション
- APIレスポンス時間（警告: 1秒, 緊急: 5秒）
- エラー率（警告: 5%, 緊急: 10%）
- リクエスト数
- アクティブ接続数

#### サービス
- 各サービスのヘルスステータス
- データベース接続状態
- 外部API接続状態

### 2. アラート設定

#### Slack通知設定
```bash
# Slack通知設定
curl -X PUT -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "slack_enabled": true,
       "slack_webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
       "system_alerts": true,
       "performance_alerts": true
     }' \
     http://localhost:8060/notifications/settings
```

#### メール通知設定
```bash
# メール通知設定
curl -X PUT -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "email_enabled": true,
       "email_recipients": ["admin@example.com"],
       "system_alerts": true,
       "daily_reports": true
     }' \
     http://localhost:8060/notifications/settings
```

### 3. 監視ダッシュボード

#### 統合監視ダッシュボード
```bash
# 監視ダッシュボードデータ取得
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/monitoring/dashboard | jq .
```

#### カスタム監視スクリプト
```bash
#!/bin/bash
# 監視スクリプト例

API_KEY="your_api_key"
API_BASE="http://localhost:8060"

# ヘルスチェック
health_status=$(curl -s -H "Authorization: Bearer $API_KEY" \
                     "$API_BASE/monitoring/health" | jq -r '.data.overall_status')

if [ "$health_status" != "healthy" ]; then
    echo "ALERT: System health is $health_status"
    # アラート送信処理
fi

# パフォーマンスチェック
cpu_percent=$(curl -s -H "Authorization: Bearer $API_KEY" \
                   "$API_BASE/monitoring/metrics" | jq -r '.data.cpu_percent')

if (( $(echo "$cpu_percent > 80" | bc -l) )); then
    echo "ALERT: High CPU usage: $cpu_percent%"
    # アラート送信処理
fi
```

## バックアップ・復旧

### 1. データバックアップ

#### Redis データバックアップ
```bash
# Redis データダンプ
docker exec PRISM-Redis redis-cli BGSAVE

# バックアップファイル確認
docker exec PRISM-Redis ls -la /data/dump.rdb

# バックアップファイルコピー
docker cp PRISM-Redis:/data/dump.rdb ./backup/redis-$(date +%Y%m%d).rdb
```

#### 設定ファイルバックアップ
```bash
# 設定ファイルバックアップ
cp .env ./backup/env-$(date +%Y%m%d).backup
cp docker-compose.yml ./backup/docker-compose-$(date +%Y%m%d).backup
cp -r config ./backup/config-$(date +%Y%m%d)
```

### 2. 復旧手順

#### サービス復旧
```bash
# 全サービス停止
docker compose down

# バックアップから復元
cp ./backup/env-20251025.backup .env
cp ./backup/docker-compose-20251025.backup docker-compose.yml

# Redis データ復元
docker cp ./backup/redis-20251025.rdb PRISM-Redis:/data/dump.rdb

# サービス再起動
docker compose up -d

# 復旧確認
docker compose ps
curl http://localhost:8060/healthz
```

## セキュリティ

### 1. セキュリティ監視

#### セキュリティイベント監視
```bash
# セキュリティイベント確認
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/security/events?limit=50" | jq .

# アクティブアラート確認
curl -H "Authorization: Bearer $API_KEY" \
     "http://localhost:8060/security/alerts?resolved=false" | jq .
```

#### レート制限監視
```bash
# レート制限統計確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/security/rate-limits | jq .
```

### 2. セキュリティ対策

#### APIキー管理
```bash
# APIキー定期変更
export API_KEY=$(openssl rand -hex 32)
echo "API_KEY=$API_KEY" >> .env

# サービス再起動
docker compose restart PRISM-API
```

#### アクセス制御
```bash
# 不正アクセスIPブロック
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "action": "block",
       "ip_address": "192.168.1.100",
       "reason": "Suspicious activity"
     }' \
     http://localhost:8060/security/ips/action
```

## パフォーマンス最適化

### 1. システム最適化

#### メモリ最適化
```bash
# メモリ使用量確認
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/metrics | jq '.data.system'

# メモリ最適化実行
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/optimize
```

#### キャッシュ最適化
```bash
# Redis キャッシュ統計
docker exec -it PRISM-Redis redis-cli info stats

# キャッシュクリア
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8060/performance/cache/clear
```

### 2. データベース最適化

#### Redis 最適化
```bash
# Redis 設定確認
docker exec -it PRISM-Redis redis-cli config get "*"

# メモリ最適化
docker exec -it PRISM-Redis redis-cli memory optimize

# 不要なキー削除
docker exec -it PRISM-Redis redis-cli --scan --pattern "temp:*" | xargs docker exec -it PRISM-Redis redis-cli del
```

## 緊急時対応

### 1. 緊急停止

```bash
# 全サービス緊急停止
docker compose down

# 特定サービス停止
docker compose stop PRISM-API
```

### 2. 緊急復旧

```bash
# 最小構成で起動
docker compose up -d PRISM-Redis PRISM-API

# ヘルスチェック
curl http://localhost:8060/healthz

# 段階的にサービス復旧
docker compose up -d PRISM-WEB
docker compose up -d PRISM-MCP
docker compose up -d PRISM-WORKER
docker compose up -d PRISM-NOTIFIER
```

### 3. 緊急連絡先

- **システム管理者**: admin@example.com
- **開発チーム**: dev@example.com
- **緊急連絡**: +81-90-1234-5678

## 更新履歴

### v2.0.0 (2025-10-25)
- 監視・ログ機能追加
- セキュリティ強化
- パフォーマンス最適化
- 運用ガイド完全版

### v1.0.0 (2025-10-20)
- 基本運用ガイド
- トラブルシューティング
- 定期メンテナンス手順
