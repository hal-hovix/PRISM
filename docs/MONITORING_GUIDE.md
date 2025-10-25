# 監視・メトリクスガイド

## 概要

PRISMシステムの監視・メトリクス機能について説明します。PrometheusとGrafanaを使用した包括的な監視システムを提供します。

**バージョン**: 2.0.0  
**更新日**: 2025年1月27日

## 監視システム構成

### アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PRISM API     │───▶│   Prometheus    │───▶│     Grafana     │
│   (メトリクス)   │    │  (データ収集)    │    │  (可視化)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Node Exporter  │    │   Alertmanager  │    │  ダッシュボード  │
│  (システム監視)  │    │  (アラート)      │    │  (監視画面)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### コンポーネント

1. **Prometheus**: メトリクスデータの収集・保存
2. **Grafana**: データの可視化・ダッシュボード
3. **Node Exporter**: システムリソース監視
4. **PRISM API**: アプリケーションメトリクス提供

## 監視対象メトリクス

### 1. システムメトリクス

- **CPU使用率**: プロセッサの使用状況
- **メモリ使用量**: RAM使用量・空き容量
- **ディスク使用量**: ストレージ使用状況
- **ネットワーク**: 送受信トラフィック
- **プロセス**: 実行中プロセスの状態

### 2. アプリケーションメトリクス

- **HTTP リクエスト数**: エンドポイント別リクエスト数
- **レスポンス時間**: API応答時間
- **エラー率**: エラーレスポンスの割合
- **アクティブ接続数**: 同時接続数
- **キャッシュヒット率**: Redisキャッシュの効率

### 3. ビジネスメトリクス

- **分類処理数**: 処理されたアイテム数
- **分類精度**: 分類の正確性
- **処理時間**: 分類処理にかかる時間
- **Notion同期**: 同期処理の状況

## セットアップ

### 1. 監視システムの起動

```bash
# 監視システムを起動
./tools/start_monitoring.sh

# または手動で起動
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### 2. アクセス先

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Node Exporter**: http://localhost:9100
- **PRISM API メトリクス**: http://localhost:8060/metrics

### 3. 設定ファイル

#### Prometheus設定 (`monitoring/prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'prism_api'
    static_configs:
      - targets: ['prism-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

#### Grafana設定

**データソース設定** (`monitoring/grafana/provisioning/datasources/prometheus.yml`):

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
```

## ダッシュボード

### 1. PRISM System Dashboard

**システム概要**
- CPU使用率
- メモリ使用量
- ディスク使用量
- ネットワークトラフィック

**API メトリクス**
- リクエスト数（エンドポイント別）
- レスポンス時間
- エラー率
- アクティブ接続数

**ビジネスメトリクス**
- 分類処理数
- 処理時間
- キャッシュヒット率

### 2. カスタムダッシュボード

Grafanaでカスタムダッシュボードを作成可能：

```json
{
  "dashboard": {
    "title": "PRISM Custom Dashboard",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

## アラート設定

### 1. Prometheus アラートルール

```yaml
# monitoring/alerts.yml
groups:
  - name: prism_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage detected"
          
      - alert: APIErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate detected"
```

### 2. Grafana アラート

Grafana内でアラートを設定：

1. **ダッシュボード** → **パネル** → **アラート**
2. **条件設定**: 閾値・評価間隔
3. **通知設定**: メール・Slack等

## メトリクスAPI

### 1. Prometheusメトリクス

```http
GET /metrics
```

**レスポンス例:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/healthz"} 100

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/healthz",le="0.1"} 95
```

### 2. カスタムメトリクス

```python
from prometheus_client import Counter, Histogram, Gauge

# カウンター
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])

# ヒストグラム
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# ゲージ
ACTIVE_CONNECTIONS = Gauge('http_requests_in_progress', 'In-progress HTTP requests', ['method', 'endpoint'])
```

## ログ監視

### 1. ログ設定

```python
# ログレベルの設定
LOG_LEVEL=INFO
LOG_FILE=logs/prism.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

### 2. ログ形式

**JSON形式** (本番環境):
```json
{
  "timestamp": "2025-01-27T10:00:00Z",
  "level": "INFO",
  "logger": "prism.api",
  "message": "Request processed",
  "method": "GET",
  "endpoint": "/healthz",
  "status_code": 200,
  "duration": 0.05
}
```

**人間可読形式** (開発環境):
```
2025-01-27 10:00:00 INFO [prism.api] Request processed GET /healthz 200 0.05s
```

## パフォーマンス監視

### 1. レスポンス時間監視

```python
# ミドルウェアでレスポンス時間を記録
@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response
```

### 2. リソース使用量監視

```python
import psutil

# CPU使用率
cpu_percent = psutil.cpu_percent(interval=1)

# メモリ使用量
memory = psutil.virtual_memory()

# ディスク使用量
disk = psutil.disk_usage('/')
```

## トラブルシューティング

### 1. 監視システムの問題

**問題**: Prometheusが起動しない
```bash
# 解決方法
docker-compose -f monitoring/docker-compose.monitoring.yml logs prometheus
# 設定ファイルの構文エラーを確認
```

**問題**: Grafanaでデータが表示されない
```bash
# 解決方法
# 1. データソースの接続確認
# 2. Prometheusのターゲット確認
# 3. ネットワーク設定確認
```

### 2. メトリクス収集の問題

**問題**: メトリクスが収集されない
```bash
# 解決方法
curl http://localhost:8060/metrics
# APIエンドポイントの確認
```

**問題**: アラートが発火しない
```bash
# 解決方法
# 1. アラートルールの構文確認
# 2. 閾値設定の確認
# 3. 評価間隔の確認
```

## ベストプラクティス

### 1. メトリクス設計

- **4つのゴールデンシグナル**: レイテンシ、トラフィック、エラー、サチュレーション
- **適切なラベル**: カーディナリティに注意
- **メトリクス名**: 命名規則に従う

### 2. アラート設定

- **適切な閾値**: ビジネス要件に基づく
- **アラート疲れの回避**: 重要なアラートのみ
- **エスカレーション**: 段階的な通知

### 3. ダッシュボード設計

- **階層化**: 概要→詳細の流れ
- **アクション可能**: 問題発見時の対応策
- **更新頻度**: リアルタイム性の確保

## 参考資料

- [Prometheus ドキュメント](https://prometheus.io/docs/)
- [Grafana ドキュメント](https://grafana.com/docs/)
- [Node Exporter ドキュメント](https://github.com/prometheus/node_exporter)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
