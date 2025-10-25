#!/bin/bash
# PRISM監視システム起動スクリプト

echo "🚀 PRISM監視システムを起動中..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 監視システムを起動
echo "📊 Prometheus + Grafanaを起動中..."
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 起動確認
echo "⏳ サービス起動を待機中..."
sleep 10

# サービス状態確認
echo "🔍 サービス状態確認:"
docker-compose -f monitoring/docker-compose.monitoring.yml ps

echo ""
echo "✅ 監視システムが起動しました！"
echo ""
echo "📊 アクセス先:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Node Exporter: http://localhost:9100"
echo ""
echo "🔧 PRISM APIメトリクス:"
echo "  - メトリクス: http://localhost:8060/metrics"
echo "  - ヘルスチェック: http://localhost:8060/healthz"
echo "  - 詳細ヘルスチェック: http://localhost:8060/healthz/detailed"
echo ""
echo "📈 Grafanaダッシュボード:"
echo "  - PRISM System Dashboard が自動的に読み込まれます"
echo ""
echo "🛑 停止する場合:"
echo "  docker-compose -f monitoring/docker-compose.monitoring.yml down"
