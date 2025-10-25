#!/bin/bash
# PRISM デプロイメントスクリプト

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 設定
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-ghcr.io}
IMAGE_NAME=${IMAGE_NAME:-prism}

log_info "🚀 PRISM デプロイメント開始"
log_info "環境: $ENVIRONMENT"
log_info "バージョン: $VERSION"
log_info "レジストリ: $DOCKER_REGISTRY"
log_info "イメージ名: $IMAGE_NAME"

# 環境変数ファイルの確認
if [ ! -f ".env.$ENVIRONMENT" ]; then
    log_error "環境変数ファイル .env.$ENVIRONMENT が見つかりません"
    log_info "env.production.example を参考に作成してください"
    exit 1
fi

# Docker Compose ファイルの確認
COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Docker Compose ファイル $COMPOSE_FILE が見つかりません"
    exit 1
fi

# 前のデプロイメントを停止
log_info "🛑 前のデプロイメントを停止中..."
docker-compose -f "$COMPOSE_FILE" down || true

# 新しいイメージをプル
log_info "📦 新しいイメージをプル中..."
docker-compose -f "$COMPOSE_FILE" pull

# サービスを起動
log_info "🚀 サービスを起動中..."
docker-compose -f "$COMPOSE_FILE" up -d

# ヘルスチェック
log_info "🔍 ヘルスチェック中..."
sleep 30

# API ヘルスチェック
API_PORT="8060"
if [ "$ENVIRONMENT" = "staging" ]; then
    API_PORT="8062"
fi

for i in {1..30}; do
    if curl -f "http://localhost:$API_PORT/healthz" > /dev/null 2>&1; then
        log_info "✅ API ヘルスチェック成功"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "❌ API ヘルスチェック失敗"
        docker-compose -f "$COMPOSE_FILE" logs PRISM-API
        exit 1
    fi
    
    log_info "⏳ API ヘルスチェック待機中... ($i/30)"
    sleep 10
done

# Web ヘルスチェック
WEB_PORT="8061"
if [ "$ENVIRONMENT" = "staging" ]; then
    WEB_PORT="8063"
fi

for i in {1..30}; do
    if curl -f "http://localhost:$WEB_PORT/" > /dev/null 2>&1; then
        log_info "✅ Web ヘルスチェック成功"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "❌ Web ヘルスチェック失敗"
        docker-compose -f "$COMPOSE_FILE" logs PRISM-WEB
        exit 1
    fi
    
    log_info "⏳ Web ヘルスチェック待機中... ($i/30)"
    sleep 10
done

# 詳細ヘルスチェック
log_info "🔍 詳細ヘルスチェック中..."
API_KEY=$(grep "API_KEY=" ".env.$ENVIRONMENT" | cut -d'=' -f2)
if [ -n "$API_KEY" ]; then
    if curl -f -H "Authorization: Bearer $API_KEY" "http://localhost:$API_PORT/healthz/detailed" > /dev/null 2>&1; then
        log_info "✅ 詳細ヘルスチェック成功"
    else
        log_warn "⚠️ 詳細ヘルスチェック失敗（認証が必要）"
    fi
fi

# メトリクスチェック
if curl -f "http://localhost:$API_PORT/metrics" > /dev/null 2>&1; then
    log_info "✅ メトリクスエンドポイント成功"
else
    log_warn "⚠️ メトリクスエンドポイント失敗"
fi

# サービス状態確認
log_info "📊 サービス状態確認:"
docker-compose -f "$COMPOSE_FILE" ps

# ログ確認
log_info "📝 最近のログ確認:"
docker-compose -f "$COMPOSE_FILE" logs --tail=20

# デプロイメント完了
log_info "🎉 デプロイメント完了!"
log_info "🌐 API: http://localhost:$API_PORT"
log_info "🌐 Web: http://localhost:$WEB_PORT"

if [ "$ENVIRONMENT" = "production" ]; then
    log_info "📊 Prometheus: http://localhost:9090"
    log_info "📈 Grafana: http://localhost:3000"
fi

log_info "🔧 管理コマンド:"
log_info "  ログ確認: docker-compose -f $COMPOSE_FILE logs -f"
log_info "  サービス停止: docker-compose -f $COMPOSE_FILE down"
log_info "  サービス再起動: docker-compose -f $COMPOSE_FILE restart"

# クリーンアップ（古いイメージの削除）
log_info "🧹 古いイメージのクリーンアップ中..."
docker image prune -f

log_info "✅ デプロイメントスクリプト完了"
