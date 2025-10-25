# PRISM v2.0.0 本番デプロイメントガイド

## 概要
PRISM v2.0.0の本番環境へのデプロイメント手順とベストプラクティスを説明します。

## 前提条件

### システム要件
- **OS**: macOS 12.0+ / Ubuntu 20.04+ / CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **メモリ**: 最低4GB、推奨8GB+
- **CPU**: 最低2コア、推奨4コア+
- **ディスク**: 最低20GB、推奨50GB+

### 必要なサービス
- **Notion API**: 有効なAPIキーとデータベースID
- **OpenAI API**: 有効なAPIキー
- **Google Calendar API**: 有効なクライアント認証情報（オプション）
- **SMTPサーバー**: メール送信用（オプション）

## デプロイメント手順

### Step 1: 環境準備

#### 1.1 リポジトリのクローン
```bash
git clone https://github.com/your-org/prism.git
cd prism
git checkout v2.0.0
```

#### 1.2 環境変数の設定
```bash
# 環境変数ファイルのコピー
cp env.example .env

# 必要な値を設定
nano .env
```

#### 1.3 セキュアキーの生成
```bash
python tools/generate_secure_keys.py
```

### Step 2: Docker環境の構築

#### 2.1 Dockerイメージのビルド
```bash
# 全サービスのビルド
docker-compose build

# 個別ビルド（必要に応じて）
docker-compose build PRISM-API
docker-compose build PRISM-WEB
docker-compose build PRISM-WORKER
docker-compose build PRISM-MCP
```

#### 2.2 サービスの起動
```bash
# 本番環境での起動
docker-compose up -d

# ログの確認
docker-compose logs -f
```

### Step 3: 監視システムの設定

#### 3.1 監視スタックの起動
```bash
# Prometheus + Grafana の起動
./tools/start_monitoring.sh

# アクセス確認
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana (admin/admin123)
```

#### 3.2 ダッシュボードの設定
1. Grafanaにログイン (http://localhost:3000)
2. デフォルトダッシュボードが自動読み込み
3. 必要に応じてカスタマイズ

### Step 4: ヘルスチェック

#### 4.1 API ヘルスチェック
```bash
# 基本ヘルスチェック
curl http://localhost:8060/healthz

# 詳細ヘルスチェック
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8060/healthz/detailed

# メトリクス確認
curl http://localhost:8060/metrics
```

#### 4.2 Web UI 確認
```bash
# Web UI アクセス
open http://localhost:8061
```

#### 4.3 パフォーマンステスト
```bash
# パフォーマンステスト実行
python tools/performance_test.py
```

### Step 5: 本番環境設定

#### 5.1 セキュリティ設定
```bash
# APIキーの更新
python tools/generate_secure_keys.py --update-env

# CORS設定の確認
grep CORS_ORIGINS .env

# JWT設定の確認
grep JWT_SECRET_KEY .env
```

#### 5.2 ログ設定
```bash
# ログディレクトリの作成
mkdir -p logs

# ログローテーション設定
sudo logrotate -f /etc/logrotate.d/prism
```

#### 5.3 バックアップ設定
```bash
# データベースバックアップスクリプト
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec PRISM-Redis redis-cli BGSAVE
docker cp PRISM-Redis:/data/dump.rdb ./backups/redis_${DATE}.rdb
EOF

chmod +x backup.sh
```

## 本番環境のベストプラクティス

### セキュリティ
- **APIキー**: 定期的なローテーション
- **HTTPS**: リバースプロキシの設定
- **ファイアウォール**: 必要なポートのみ開放
- **アクセス制御**: IP制限の設定

### パフォーマンス
- **リソース制限**: Docker コンテナのリソース制限
- **キャッシュ戦略**: Redis キャッシュの最適化
- **ロードバランシング**: 複数インスタンスの配置
- **CDN**: 静的ファイルの配信最適化

### 監視・ログ
- **メトリクス**: Prometheus での継続監視
- **アラート**: しきい値ベースのアラート設定
- **ログ集約**: 中央集約システムの構築
- **ダッシュボード**: リアルタイム監視

### バックアップ・復旧
- **定期バックアップ**: 自動バックアップの設定
- **復旧テスト**: 定期的な復旧テスト
- **災害復旧**: 地理的分散の検討
- **バージョン管理**: 設定のバージョン管理

## トラブルシューティング

### よくある問題

#### 1. サービス起動失敗
```bash
# ログ確認
docker-compose logs PRISM-API

# リソース確認
docker stats

# 設定確認
docker-compose config
```

#### 2. メモリ不足
```bash
# メモリ使用量確認
free -h
docker stats

# コンテナ制限設定
# docker-compose.yml で memory_limit を設定
```

#### 3. ネットワーク問題
```bash
# ネットワーク確認
docker network ls
docker network inspect prism_prism_net

# ポート確認
netstat -tlnp | grep :8060
```

#### 4. 認証エラー
```bash
# APIキー確認
grep API_KEY .env

# 認証テスト
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8060/healthz/detailed
```

### ログ分析
```bash
# エラーログの確認
grep ERROR logs/prism.log

# パフォーマンスログの確認
grep "slow" logs/prism.log

# アクセスログの確認
grep "GET\|POST" logs/prism.log
```

## メンテナンス

### 定期メンテナンス
- **週次**: ログローテーション、ディスク使用量確認
- **月次**: セキュリティアップデート、パフォーマンス確認
- **四半期**: バックアップテスト、災害復旧テスト

### アップデート手順
```bash
# 1. バックアップ作成
./backup.sh

# 2. 新バージョンの取得
git pull origin main

# 3. 依存関係の更新
pip install -r requirements.txt

# 4. サービスの再起動
docker-compose down
docker-compose up -d

# 5. ヘルスチェック
curl http://localhost:8060/healthz
```

## まとめ

PRISM v2.0.0の本番デプロイメントは、セキュリティ、パフォーマンス、監視、バックアップの観点から包括的に設計されています。本ガイドに従うことで、安定した本番環境を構築・運用できます。

継続的な監視とメンテナンスにより、高品質なサービス提供を実現しましょう。
